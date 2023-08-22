import threading
import shutil
import sounddevice as sd
import soundfile as sf
import os

from queue import Queue
from winsound import PlaySound
from pydub import AudioSegment

from tortoise_api import Tortoise_API
from tortoise_api import filter_paragraph

tortoise = Tortoise_API()


def play_audio_from_queue(audio_queue, free_slots):
    while True:
        audio_file, slot = audio_queue.get()
        if audio_file == "stop":
            break
        data, sample_rate = sf.read(audio_file)
        # sd.play(data, sample_rate)
        # sd.wait()
        audio_queue.task_done()
        free_slots.put(slot)

def append_to_audiobook(audio_path):
    if os.path.isfile('audiobook.wav'):
        sound1 = AudioSegment.from_wav("audiobook.wav")
        sound2 = AudioSegment.from_wav(audio_path)
        combined_sounds = sound1 + sound2
    else:
        # If 'audiobook.wav' doesn't exist, create it with the first audio clip
        combined_sounds = AudioSegment.from_wav(audio_path)
    combined_sounds.export("audiobook.wav", format="wav")

def create_and_queue_audio(sentences, audio_queue, free_slots):
    for sentence in sentences[:5]:
        slot = free_slots.get()
        audio_path = generate_sound(sentence)
        # Append generated audio to audiobook
        append_to_audiobook(audio_path)
        try:
            shutil.copy2(audio_path, f'temp{slot}.wav')
        except IOError as e:
            print(f"Unable to copy file {audio_path} to temp.wav. Error: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

        audio_file = f'temp{slot}.wav'
        
        audio_queue.put((audio_file, slot))

    return len(sentences[:5])


def generate_sound(sentence):
    return tortoise.call_api(sentence, is_queue=False)

def load_sentences(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        paragraphs = content.split('\n\n')  # Split content into paragraphs
        filtered_sentences = []
        for paragraph in paragraphs:
            filtered_list = filter_paragraph(paragraph)
            filtered_sentences.extend(filtered_list)
    return filtered_sentences

def main():
    file_path = 'text.txt'
    sentences = load_sentences(file_path)
    
    audio_queue = Queue()
    free_slots = Queue()

    for i in range(1, 6):
        free_slots.put(i)

    total_processed = create_and_queue_audio(sentences, audio_queue, free_slots)
    audio_thread = threading.Thread(target=play_audio_from_queue, args=(audio_queue, free_slots))
    audio_thread.start()

    while total_processed < len(sentences):
        processed = create_and_queue_audio(sentences[total_processed:], audio_queue, free_slots)
        total_processed += processed

    audio_queue.join()

if __name__ == '__main__':
    main()
