import requests
import concurrent.futures
from queue import Queue
import threading
import os
import sounddevice as sd
import soundfile as sf
import yaml
import re

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
        max_retries = 5
        
        for attempt in range(max_retries):
            for port in range(7860, 7866):
                try:
                    url = f"http://127.0.0.1:{port}/run/generate"
                    print(f"Calling API with sentence: <{sentence}>")
                    response = requests.post(url, json={
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

                    if is_queue:
                        slot = self.free_slots.get()
                        self.audio_queue.put((audio_path, slot))
                    else:
                        return audio_path

                except requests.ConnectionError:
                    print(f"Failed to connect to port {port}, trying next port")
                except requests.Timeout:
                    print(f"Request timed out on port {port}, trying next port")
                except requests.RequestException as e:  # Catch any other requests exceptions
                    print(f"An error occurred on port {port}: {e}")
                except Exception as e:  # Catch non-requests exceptions
                    print(f"An unexpected error occurred: {e}")
            
            print(f"Attempt {attempt + 1} failed, retrying...")  # Log the retry attempt
            import time
            # time.sleep(1)  # Optional: add a delay between retries
        
        print(f"Failed to connect after {max_retries} attempts")
        return None

            

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

import re

def filter_paragraph(paragraph):
    lines = paragraph.strip().split('\n')
    
    filtered_list = []
    i = 0
    while i < len(lines):
        split_sentences = lines[i].split('. ')
        for part_sentence in split_sentences:
            if not part_sentence:
                continue

            line = part_sentence.strip()

            while line.endswith(",") and (i + 1) < len(lines):
                i += 1
                line += " " + lines[i].split('. ')[0].strip()

            # Remove square brackets and strip the line again
            line = re.sub(r'\[|\]', '', line).strip()

            # Only append lines that contain at least one alphabetic character
            if line and any(c.isalpha() for c in line):
                filtered_list.append(line)

        i += 1

    return filtered_list


def load_sentences(file_path) -> list:
    '''
    Utility function for toroise to load sentences from a text file path

    Args:
        file_path(str) : path to some text file

    '''
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        paragraphs = content.split('\n\n')  # Split content into paragraphs
        filtered_sentences = []
        for paragraph in paragraphs:
            filtered_list = filter_paragraph(paragraph)
            filtered_sentences.extend(filtered_list)
    return filtered_sentences

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
