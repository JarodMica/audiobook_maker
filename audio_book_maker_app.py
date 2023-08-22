import os
import pickle
import tkinter as tk
import sounddevice as sd
import soundfile as sf
import threading
import shutil

from tkinter import filedialog
from pydub import AudioSegment
from winsound import PlaySound

from tortoise_api import Tortoise_API
from tortoise_api import filter_paragraph


def load_sentences(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        paragraphs = content.split('\n\n')  # Split content into paragraphs
        filtered_sentences = []
        for paragraph in paragraphs:
            filtered_list = filter_paragraph(paragraph)
            filtered_sentences.extend(filtered_list)
    return filtered_sentences


def save_checkpoint(checkpoint_file, sentence_index, audio_book):
    checkpoint_data = {'sentence_index': sentence_index, 'audio_book': audio_book}
    with open(checkpoint_file, 'wb') as file:
        pickle.dump(checkpoint_data, file)

def load_checkpoint(checkpoint_file):
    if os.path.isfile(checkpoint_file):
        with open(checkpoint_file, 'rb') as file:
            checkpoint_data = pickle.load(file)
            sentence_index = checkpoint_data['sentence_index']
            audio_book = checkpoint_data['audio_book']
    else:
        sentence_index = 0
        audio_book = []
    return sentence_index, audio_book

class AudioBookApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.tortoise = Tortoise_API()

        self.file_path = ""
        self.sentences = []
        self.sentence_index = 0
        self.audio_book = []
        self.checkpoint_file = "audio_book.pkl"
        self.audio_book_history = []
        self.prev_sentence_index = None
        self.next_sentence_index = None

        self.title("Audio Book Maker")
        self.geometry("400x500")

        self.load_button = tk.Button(self, text="Load Sentences", command=self.load_text_file)
        self.load_button.pack(pady=5)

        self.start_from_checkpoint_button = tk.Button(self, text="Start from Checkpoint", command=self.start_from_checkpoint)
        self.start_from_checkpoint_button.pack(pady=5)

        self.pause_label = tk.Label(self, text="Sentence Pause")
        self.pause_label.pack()
        self.pause_scale = tk.Scale(self, from_=0.00, to=5.00, resolution=0.1, orient=tk.HORIZONTAL)
        self.pause_scale.set(1.00)  # Set default value to 1.0
        self.pause_scale.pack(pady=5)

        self.play_button = tk.Button(self, text="Play", command=self.play_sentence)
        self.play_button.pack(pady=5)

        self.add_button = tk.Button(self, text="Add to Audio Book", command=self.add_sentence)
        self.add_button.pack(pady=5)

        self.back_button = tk.Button(self, text="← Go Back", command=self.go_back)
        self.back_button.pack(padx=5)

        self.forward_button = tk.Button(self, text="Go Forward→", command=self.go_forward)
        self.forward_button.pack(padx=5)

        self.undo_button = tk.Button(self, text="Undo Last Change", command=self.undo_last_change)
        self.undo_button.pack(pady=5)

        self.current_sentence = tk.Text(self, height=4, wrap=tk.WORD)
        self.current_sentence.pack(pady=5)


    def add_audio_book_history(self):
        self.audio_book_history.append(self.audio_book[:])

    def load_text_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        self.sentences = load_sentences(self.file_path)

    def start_from_checkpoint(self):
        if os.path.isfile(self.checkpoint_file):
            self.sentence_index, self.audio_book = load_checkpoint(self.checkpoint_file)

    def play_sentence(self):
        out_file = self.generate_sound(self.sentences[self.sentence_index])
        try:
            shutil.copy2(out_file, 'temp.wav')
            self.play_audio('temp.wav')
        except IOError as e:
            print(f"Unable to copy file {out_file} to temp.wav. Error: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        self.current_sentence.delete('1.0', tk.END)  # Remove previous content
        self.current_sentence.insert(tk.END, self.sentences[self.sentence_index])  # Insert the current sentence

    def add_sentence(self):
        self.add_audio_book_history()
        pause = 1000*self.pause_scale.get()
        out_file = "temp.wav"
        sound = AudioSegment.from_file(out_file, format="wav")
        self.audio_book.append(sound)
        pause = AudioSegment.silent(duration=pause)  # default 1-second pause
        self.audio_book.append(pause)  # Add the pause to the audio_book
        audio_book_file = "audio_book.wav"
        concatenated_audio = sum(self.audio_book, AudioSegment.empty())
        concatenated_audio.export(audio_book_file, format='wav')
        os.remove(out_file)
        self.sentence_index += 1
        self.save_checkpoint()

    def undo_last_change(self):
        if self.audio_book_history:
            self.audio_book = self.audio_book_history.pop()
            audio_book_file = "audio_book.wav"
            concatenated_audio = sum(self.audio_book, AudioSegment.empty())
            concatenated_audio.export(audio_book_file, format='wav')
            self.sentence_index -= 1
            self.save_checkpoint()

    def go_back(self):
        if self.sentence_index > 0:
            self.prev_sentence_index = self.sentence_index - 1
            self.sentence_index = self.prev_sentence_index
            self.play_sentence()

    def go_forward(self):
        if self.sentence_index < len(self.sentences) - 1:
            self.next_sentence_index = self.sentence_index + 1
            self.sentence_index = self.next_sentence_index
            self.play_sentence()

    def save_checkpoint(self):
        save_checkpoint(self.checkpoint_file, self.sentence_index, self.audio_book)

    def generate_sound(self, sentence):
        return self.tortoise.call_api(sentence, is_queue=False)
    
    def play_audio(self, audio_path):
        def play():
            data, sample_rate = sf.read(audio_path)
            sd.play(data, sample_rate)
            sd.wait()
        self.update()  # Update Tkinter mainloop
        threading.Thread(target=play).start()
        self.update()  # Update Tkinter mainloop again
        

if __name__ == "__main__":
    app = AudioBookApp()
    app.mainloop()