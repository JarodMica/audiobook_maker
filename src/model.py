# model.py

import os
import json
import shutil
from pydub import AudioSegment
import pyttsx3
import re
import tempfile
import tts_engines  # Import your TTS_engines module


class AudiobookModel:
    def __init__(self):
        self.text_audio_map = {}
        self.settings = {}
        self.voice_folder_path = "voice_models"
        self.index_folder_path = "voice_indexes"
        self.current_sentence_idx = 0

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #   Data Loading and Saving Methods
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def load_settings(self):
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as json_file:
                self.settings = json.load(json_file)
                return self.settings
        return {}
    
    def get_tts_engines(self):
        # Load available TTS engines from the tts_config.json
        tts_config = self.load_tts_config('tts_config.json')
        return [engine['name'] for engine in tts_config.get('tts_engines', [])]

    def load_tts_config(self, config_path):
        if not os.path.exists(config_path):
            return {}
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def save_settings(self, background_image=None):
        self.settings['background_image'] = background_image
        with open('settings.json', 'w') as json_file:
            json.dump(self.settings, json_file)

    def load_sentences(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            paragraphs = content.split('\n\n')  # Split content into paragraphs
            filtered_sentences = []
            for paragraph in paragraphs:
                filtered_list = self.filter_paragraph(paragraph)
                filtered_sentences.extend(filtered_list)
        return filtered_sentences

    def filter_paragraph(self, paragraph):
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

    def save_text_audio_map(self, directory_path):
        # Specify the path for the text_audio_map file
        map_file_path = os.path.join(directory_path, "text_audio_map.json")

        # Open the file in write mode
        with open(map_file_path, 'w', encoding="utf-8") as map_file:
            # Convert the text_audio_map dictionary to a JSON string and write it to the file
            json.dump(self.text_audio_map, map_file, ensure_ascii=False, indent=4)

    def load_text_audio_map(self, directory_path):
        map_file_path = os.path.join(directory_path, "text_audio_map.json")
        if not os.path.exists(map_file_path):
            raise FileNotFoundError("The selected directory is not a valid Audiobook Directory.")
        with open(map_file_path, 'r', encoding="utf-8") as map_file:
            self.text_audio_map = json.load(map_file)
        return self.text_audio_map

    def create_audio_text_map(self, directory_path, sentences_list):
        audio_map_path = os.path.join(directory_path, 'text_audio_map.json')
        new_text_audio_map = {}
        for idx, sentence in enumerate(sentences_list):
            generated = False
            audio_path = ""
            new_text_audio_map[str(idx)] = {"sentence": sentence, "audio_path": audio_path, "generated": generated}
        self.text_audio_map = new_text_audio_map
        self.save_json(audio_map_path, new_text_audio_map)

    def save_json(self, file_path, data):
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def load_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #   Audiobook Generation Methods
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    def load_selected_tts_engine(self, chosen_tts_engine, **kwargs):
        self.tts_engine = tts_engines.load_tts_engine(chosen_tts_engine, **kwargs)
        return self.tts_engine
        

    def generate_audio_for_sentence_threaded(self, directory_path, report_progress_callback, voice_parameters, sentence_generated_callback):
        # audio_map_path = os.path.join(directory_path, 'text_audio_map.json')
        self.load_text_audio_map(directory_path)

        total_sentences = len(self.text_audio_map)
        generated_count = sum(1 for entry in self.text_audio_map.values() if entry['generated'])

        # Iterate through each entry in the map
        for idx, entry in self.text_audio_map.items():
            sentence = entry['sentence']
            new_audio_path = entry['audio_path']
            generated = entry['generated']

            # Check if audio is already generated
            if not generated:
                # Generate audio for the sentence
                # Entry point for new logic to select between TTS engines
                audio_path = self.generate_audio_proxy(sentence, voice_parameters)

                # Check if audio is successfully generated
                if audio_path:
                    file_idx = 0
                    new_audio_path = os.path.join(directory_path, f"audio_{idx}.wav")
                    while os.path.exists(new_audio_path):
                        file_idx += 1
                        new_audio_path = os.path.join(directory_path, f"audio_{idx}_{file_idx}.wav")
                    os.rename(audio_path, new_audio_path)
                    # Update the audio path and set generated to true
                    self.text_audio_map[idx]['audio_path'] = new_audio_path
                    self.text_audio_map[idx]['generated'] = True

                    # Increment the generated_count
                    generated_count += 1

                    # Save the updated map back to the file
                    self.save_text_audio_map(directory_path)

                    # Call the sentence_generated_callback
                    sentence_generated_callback(int(idx), sentence)

            # Report progress
            progress_percentage = int((generated_count / total_sentences) * 100)
            report_progress_callback(progress_percentage)

    def generate_audio_proxy(self, sentence, voice_parameters):
        tts_engine_name = voice_parameters.get('tts_engine', 'pyttsx3')

        # Generate a unique temporary file name
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_path = tmp_file.name

        # Now call tts_engines.generate_audio(self.tts_engine, sentence, voice_parameters, tts_engine_name, audio_path)
        success = tts_engines.generate_audio(self.tts_engine, sentence, voice_parameters, tts_engine_name, audio_path)

        if success:
            return audio_path
        else:
            return None

    def export_audiobook(self, directory_path, pause_duration):
        dir_name = os.path.basename(directory_path)
        idx = 0

        # Ensure 'exported_audiobooks' directory exists
        exported_dir = os.path.join(directory_path, "exported_audiobooks")
        if not os.path.exists(exported_dir):
            os.makedirs(exported_dir)

        # Find a suitable audio file name with an incrementing suffix
        while True:
            new_audiobook_name = f"{dir_name}_audiobook_{idx}.wav"
            new_audiobook_path = os.path.join(exported_dir, new_audiobook_name)
            if not os.path.exists(new_audiobook_path):
                break  # Exit the loop once a suitable name is found
            idx += 1

        output_filename = new_audiobook_path

        # Load the JSON file
        audio_map_path = os.path.join(directory_path, 'text_audio_map.json')
        if not os.path.exists(audio_map_path):
            raise FileNotFoundError("The selected directory is not a valid Audiobook Directory.")

        with open(audio_map_path, 'r', encoding='utf-8') as file:
            text_audio_map = json.load(file)

        # Sort the keys (converted to int), then get the corresponding audio paths
        sorted_audio_paths = [text_audio_map[key]['audio_path'] for key in sorted(text_audio_map, key=lambda k: int(k))]

        combined_audio = AudioSegment.empty()  # Create an empty audio segment

        pause_length = pause_duration * 1000  # convert to milliseconds
        silence = AudioSegment.silent(duration=pause_length)  # Create a silent audio segment of pause_length

        for audio_path in sorted_audio_paths:
            audio_segment = AudioSegment.from_wav(audio_path)
            combined_audio += audio_segment + silence  # Append the audio segment followed by silence

        # If you don't want silence after the last segment, you might need to trim it
        if pause_length > 0:
            combined_audio = combined_audio[:-pause_length]

        # Export the combined audio
        combined_audio.export(output_filename, format="wav")

        print(f"Combined audiobook saved as {output_filename}")
        return output_filename

    def update_audiobook(self, directory_path, new_sentences_list, generate_new_audio, voice_parameters):
        audio_map_path = os.path.join(directory_path, 'text_audio_map.json')
        if not os.path.exists(audio_map_path):
            raise FileNotFoundError("The selected directory is not a valid Audiobook Directory.")

        # Load existing text_audio_map
        with open(audio_map_path, 'r', encoding='utf-8') as file:
            text_audio_map = json.load(file)

        reverse_map = {item['sentence']: idx for idx, item in text_audio_map.items()}

        # Generate updated map
        new_text_audio_map = {}
        deleted_sentences = set(text_audio_map.keys())
        for new_idx, sentence in enumerate(new_sentences_list):
            if sentence in reverse_map:  # Sentence exists in old map
                old_idx = reverse_map[sentence]
                new_text_audio_map[str(new_idx)] = text_audio_map[old_idx]
                deleted_sentences.discard(old_idx)  # Remove index from set of deleted sentences
            else:  # New sentence
                generated = False
                new_audio_path = ""
                new_text_audio_map[str(new_idx)] = {"sentence": sentence, "audio_path": new_audio_path, "generated": generated}

        # Handle deleted sentences and their audio files
        for old_idx in deleted_sentences:
            old_audio_path = text_audio_map[old_idx]['audio_path']
            if os.path.exists(old_audio_path):
                os.remove(old_audio_path)  # Delete the audio file

        self.text_audio_map = new_text_audio_map
        self.save_text_audio_map(directory_path)

        if generate_new_audio:
            self.generate_audio_for_sentence_threaded(directory_path, lambda x: None, voice_parameters)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #   Voice Models and Settings
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def get_voice_models(self):
        if os.path.exists(self.voice_folder_path) and os.path.isdir(self.voice_folder_path):
            voice_model_files = [file for file in os.listdir(self.voice_folder_path) if file.endswith(".pth")]
            return voice_model_files
        return []

    def get_voice_indexes(self):
        if os.path.exists(self.index_folder_path) and os.path.isdir(self.index_folder_path):
            voice_index_files = [file for file in os.listdir(self.index_folder_path) if file.endswith(".index")]
            return voice_index_files
        return []

    def save_generation_settings(self, directory_path, generation_settings):
        generation_settings_path = os.path.join(directory_path, "generation_settings.json")
        self.save_json(generation_settings_path, generation_settings)

    def load_generation_settings(self, directory_path):
        generation_settings_path = os.path.join(directory_path, "generation_settings.json")
        if os.path.exists(generation_settings_path):
            return self.load_json(generation_settings_path)
        else:
            return {}

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #   Utility Methods
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def set_background_image(self, file_name):
        if not os.path.exists('image_backgrounds'):
            os.makedirs('image_backgrounds')
        image_name = os.path.basename(file_name)
        destination_path = os.path.join('image_backgrounds', image_name)
        if os.path.abspath(file_name) != os.path.abspath(destination_path):
            shutil.copy2(file_name, destination_path)
        self.save_settings(background_image=destination_path)
        return destination_path

    def clear_background_image(self):
        self.save_settings(background_image=None) 
