import threading
import shutil
import sounddevice as sd
import soundfile as sf
import os
import datetime

from queue import Queue
from winsound import PlaySound
from pydub import AudioSegment
from rvc_infer import rvc_convert

from tortoise_api import Tortoise_API
from tortoise_api import filter_paragraph

tortoise = Tortoise_API()


def play_audio_from_queue(audio_queue, free_slots):
    while True:
        audio_file, slot = audio_queue.get()
        if audio_file == "stop":
            break
        data, sample_rate = sf.read(audio_file)
        sd.play(data, sample_rate)
        sd.wait()
        audio_queue.task_done()
        free_slots.put(slot)


def save_individual_audio(audio_path, sentence_number, folder_path, date_string):
    destination_path = os.path.join(folder_path, f'audiobook_{date_string}_{sentence_number}.wav')
    shutil.copy2(audio_path, destination_path)

def create_and_queue_audio(sentences, audio_queue, free_slots, folder_path, date_string, model_path=None):
    for index, sentence in enumerate(sentences[:2]):
        slot = free_slots.get()
        audio_path = generate_sound(sentence, model_path)
        # Save generated audio as individual audiobook
        save_individual_audio(audio_path, index + 1, folder_path, date_string)

        try:
            shutil.copy2(audio_path, f'temp{slot}.wav')
        except IOError as e:
            print(f"Unable to copy file {audio_path} to temp.wav. Error: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

        audio_file = f'temp{slot}.wav'
        
        audio_queue.put((audio_file, slot))

    return len(sentences[:2])


def generate_sound(sentence, model_path):
    audio_path = tortoise.call_api(sentence, is_queue=False)
    return rvc_convert(model_path=model_path, f0_up_key=0, input_path=audio_path)

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
    model_path = "rui48k"
    
    audio_queue = Queue()
    free_slots = Queue()

    for i in range(1, 6):
        free_slots.put(i)
        
    # create new directory
    now = datetime.datetime.now()
    date_string = now.strftime("%Y%m%d%H%M%S")
    folder_name = f'audiobook_{date_string}'
    folder_path = os.path.join('audiobooks', folder_name)
    os.makedirs(folder_path, exist_ok=True)

    total_processed = create_and_queue_audio(sentences, audio_queue, free_slots, folder_path, date_string, model_path=model_path)
    audio_thread = threading.Thread(target=play_audio_from_queue, args=(audio_queue, free_slots))
    audio_thread.start()

    while total_processed < len(sentences):
        processed = create_and_queue_audio(sentences[total_processed:], audio_queue, free_slots, folder_path, date_string, model_path=model_path)
        total_processed += processed

    audio_queue.join()


if __name__ == '__main__':
    main()
