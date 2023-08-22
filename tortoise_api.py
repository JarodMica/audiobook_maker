import requests
import concurrent.futures
from queue import Queue
import threading
import os
import sounddevice as sd
import soundfile as sf
import yaml

class Tortoise_API:
    '''
    API calls to the tortoise GUI using requests.  Must have an open instance of
    tortoise TTS GUI running or else nothing will happen. For most cases, to use this
    you need to use filter_paragraph() to splice text into a list of sentences, then
    feed that list 1-by-1 into call_api.  The idea is to speed up the process so that you can
    generate audio while audio is being spoken
    '''
    def __init__(self):
        # Actually only necessary if you're using run(), could clean up code later
        self.audio_queue = Queue()
        self.free_slots = Queue()
        self.semaphore = threading.Semaphore(1)

    def call_api(self, sentence, is_queue=False):
        '''
        Makes a request to the Tortoise TTS GUI.  Relies on tort.yaml, so make sure it's set-up

        Args:
            sentence (str) : Text to be converted to speech
            is_queue (bool) : Only set to True if using as standalone script.  Uses built in queue
                            system to queue up 6 samples of audio to be read out loud.
        
        Returns:
            audio_path (str) : Path of the audio to be played
        '''
        tort_conf = load_config()
    
        while True:
            try:
                print(f"Calling API with sentence: {sentence}")
                response = requests.post("http://127.0.0.1:7860/run/generate", json={
                    "data": [
                        f"{sentence}", #prompt
                        tort_conf['delimiter'], #delimter
                        tort_conf['emotion'], #emotion
                        tort_conf['custom_emotion'], #custom emotion
                        tort_conf['voice_name'], #voice name
                        {"name": tort_conf['audio_file'],"data":"data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="},
                        tort_conf['voice_chunks'], #voice chunks
                        tort_conf['candidates'], #candidates
                        tort_conf['seed'], #seed
                        tort_conf['samples'], #samples
                        tort_conf['iterations'], #iterations
                        tort_conf['temperature'], #temp
                        tort_conf['diffusion_sampler'],
                        tort_conf['pause_size'],
                        tort_conf['cvvp_weight'],
                        tort_conf['top_p'],
                        tort_conf['diffusion_temp'],
                        tort_conf['length_penalty'],
                        tort_conf['repetition_penalty'],
                        tort_conf['conditioning_free_k'],
                        tort_conf['experimental_flags'],
                        False,
                        False,
                    ]
                }).json()

                audio_path = response['data'][2]['choices'][0]
                print(f"API response received with audio path: {audio_path}")
                break
            except:
                # add something to error after x amount of tries
                print("tortoise failed, trying again")
                continue

        if is_queue:
            slot = self.free_slots.get()
            self.audio_queue.put((audio_path, slot))
        else:
            return audio_path

    def play_audio_from_queue(self):
        while True:
            audio_file, slot = self.audio_queue.get()
            if audio_file == "stop":
                self.audio_queue.task_done()
                break
            data, sample_rate = sf.read(audio_file)
            sd.play(data, sample_rate)
            sd.wait()
            os.remove(audio_file)
            self.audio_queue.task_done()
            self.free_slots.put(slot)

    # Usually only ran if using this as a standalone script, most likely you won't be
    def run(self, sentences):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for i in range(1, 6):
                self.free_slots.put(i)

            audio_thread = threading.Thread(target=self.play_audio_from_queue)
            audio_thread.start()

            # Wait for each API call to complete before starting the next one
            for sentence in sentences:
                future = executor.submit(self.call_api, sentence)
                concurrent.futures.wait([future])

            self.audio_queue.join()
            self.audio_queue.put(("stop", None))

def load_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_file = os.path.join(current_dir, "tort.yaml")

    with open(yaml_file, "r") as file:
        tort_conf = yaml.safe_load(file)

    return tort_conf

def filter_paragraph(paragraph, sentence_len = 130):
    '''
    Filters a large body of text into a list of strings to reduce the load
    sent over to the API.  Is needed to make the API calls faster and used for Tortoise

    Args:
        paragraph (str) : Any body of text
        sentence_len (int) : minimum length of sentence

    Returns:
        filtered_list (tuple) :  A list of sentences 

    '''
    paragraph = paragraph.replace('\n', ' ')  # Replace new lines with spaces
    sentences = paragraph.split('. ')
    filtered_list = []
    current_sentence = ""

    for sentence in sentences:
        if len(current_sentence + sentence) <= sentence_len:
            current_sentence += sentence + '. '
        else:
            if current_sentence.strip():  # Check if the current sentence is not just spaces
                filtered_list.append(current_sentence.strip())
            current_sentence = sentence + '. '

    if current_sentence.strip():  # Check if the current sentence is not just spaces
        filtered_list.append(current_sentence.strip())

    return filtered_list

def read_paragraph_from_file(file_path):
    with open(file_path, 'r') as file:
        paragraph = file.read()
    return paragraph

if __name__ == "__main__":
    file_path = "story.txt"
    paragraph = read_paragraph_from_file(file_path)
    filtered_paragraph = filter_paragraph(paragraph)
    player = Tortoise_API()
    player.run(filtered_paragraph)
