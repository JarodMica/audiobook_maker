# model.py

import os
import json
import math
import shutil
from pydub import AudioSegment
import pyttsx3
import re
import tempfile
import tts_engines  # Import your TTS_engines module
import s2s_engines
from collections import defaultdict
from pathlib import Path
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from typing import List

class AudiobookModel:
    def __init__(self):
        self.text_audio_map = {}
        self.settings = {}
        self.voice_folder_path = "voice_models"
        self.index_folder_path = "voice_indexes"
        self.current_sentence_idx = 0
        self.speakers = {
        1: {'name': 'Narrator', 'color': '#FFFFFF', 'settings': {}}
    }
        self.current_tts_engine_name = None
        self.current_speaker_id = None
        self.current_voice_parameters = None
        self.tts_engine = None
        self.filepath = None
        
        self.current_s2s_engine_name = None
        self.current_s2s_speaker_id = None
        self.current_s2s_parameters = None
        self.s2s_engine = None

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
        tts_config = self.load_config(os.path.join('configs', 'tts_config.json'))
        return [engine['name'] for engine in tts_config.get('tts_engines', [])]
    
    def get_rvc_config(self):
        rvc_config = self.load_config(os.path.join('configs', 'rvc_config.json'))
        return rvc_config


    def load_config(self, config_path):
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
    
    def update_text_audio_map(self, sentences_list):
        # Update self.text_audio_map to include any new sentences
        # Retain existing mappings for sentences that are already there

        new_text_audio_map = {}
        sentence_to_existing_idx = {item['sentence']: idx for idx, item in self.text_audio_map.items()}

        for idx, sentence in enumerate(sentences_list):
            if sentence in sentence_to_existing_idx:
                existing_idx = sentence_to_existing_idx[sentence]
                # Use existing mapping, but update index
                item = self.text_audio_map[existing_idx]
                new_text_audio_map[str(idx)] = item
            else:
                # New sentence
                generated = False
                audio_path = ""
                new_text_audio_map[str(idx)] = {
                    "sentence": sentence,
                    "audio_path": audio_path,
                    "generated": generated,
                    "speaker_id": 1  # Default speaker
                }
        self.text_audio_map = new_text_audio_map


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
        new_text_audio_map = {}
        for idx, sentence in enumerate(sentences_list):
            generated = False
            audio_path = ""
            new_text_audio_map[str(idx)] = {
                "sentence": sentence,
                "audio_path": audio_path,
                "generated": generated,
                "speaker_id": 1  # Default speaker
            }
        self.text_audio_map = new_text_audio_map
        # Do not save to file yet since directory_path is empty

        
    def update_speakers(self, speakers):
        self.speakers = speakers
        
    def assign_speaker_to_sentence(self, idx, speaker_id, regen_mode):
        idx_str = str(idx)
        if idx_str in self.text_audio_map:
            self.text_audio_map[idx_str]['speaker_id'] = speaker_id
            if regen_mode:
                self.text_audio_map[idx_str]['generated'] = False
            # Optionally, save the updated map
            # self.save_text_audio_map(directory_path)

    def save_json(self, file_path, data):
        def default_serializer(obj):
            if isinstance(obj, QColor):
                return obj.name()  # Convert QColor to hex string
            elif isinstance(obj, int):  # Handle Qt.GlobalColor
                return QColor(obj).name()  # Convert int (GlobalColor) to hex string
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4, default=default_serializer)


    def load_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #   Audiobook Generation Methods
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    def load_selected_tts_engine(self, chosen_tts_engine, speaker_id, **kwargs):
        # Check if the TTS engine is already loaded with these parameters
        if (self.current_tts_engine_name == chosen_tts_engine and
            self.current_speaker_id == speaker_id and
            self.current_voice_parameters == kwargs):
            # Already loaded, skip loading
            return self.tts_engine
        else:
            # Load the TTS engine
            self.tts_engine = tts_engines.load_tts_engine(chosen_tts_engine, **kwargs)
            # Store current parameters
            self.current_tts_engine_name = chosen_tts_engine
            self.current_speaker_id = speaker_id
            self.current_voice_parameters = kwargs
            return self.tts_engine
        
    def load_selected_s2s_engine(self, chosen_s2s_engine, speaker_id, **kwargs):
        # Check if the s2s engine is already loaded with these parameters
        if (self.current_s2s_engine_name == chosen_s2s_engine and
            self.current_s2s_speaker_id == speaker_id and
            self.current_s2s_parameters == kwargs):
            # Already loaded, skip loading
            return True
        else:
            try:
                # Load the s2s engine
                self.s2s_engine = s2s_engines.load_s2s_engine(chosen_s2s_engine, **kwargs)
                if self.s2s_engine == None:
                    return False
                # Store current parameters
                self.current_s2s_engine_name = chosen_s2s_engine
                self.current_s2s_speaker_id = speaker_id
                self.current_s2s_parameters = kwargs
                return True
            except Exception as e:
                # Handle exception, perhaps log it
                print(f"Failed to load s2s engine '{chosen_s2s_engine}': {e}")
                return False

        

    def generate_audio_for_sentence_threaded(self, directory_path, is_continue, report_progress_callback, sentence_generated_callback, should_stop_callback=None):
        self.load_generation_settings(directory_path)
        self.load_text_audio_map(directory_path)
        total_sentences = len(self.text_audio_map)
        if is_continue:
            generated_count = sum(1 for entry in self.text_audio_map.values() if entry['generated'])
            if generated_count == total_sentences:
                return
        else:
            generated_count = 0

        sentences_by_speaker = defaultdict(list)
        for idx, entry in self.text_audio_map.items():
            speaker_id = entry.get('speaker_id', 1)
            sentences_by_speaker[speaker_id].append((idx, entry))

        # For each speaker, generate audio
        for speaker_id, entries in sentences_by_speaker.items():
            # Load speaker settings
            speaker = self.speakers.get(speaker_id, {})
            speaker_settings = speaker.get('settings', {})
            # Load TTS engine with speaker-specific settings
            tts_engine_name = speaker_settings.get('tts_engine', 'pyttsx3')
            self.load_selected_tts_engine(tts_engine_name, speaker_id, **speaker_settings)
            
            use_s2s = speaker_settings.get('use_s2s', False)
            if use_s2s:
                s2s_engine_name = speaker_settings.get('s2s_engine', None)
                if s2s_engine_name:
                    s2s_parameters = speaker_settings.copy()
                    s2s_validated = self.load_selected_s2s_engine(s2s_engine_name, speaker_id, **s2s_parameters)
                else:
                    s2s_validated = False
            else:
                s2s_validated = False
            
            # Generate audio for sentences assigned to this speaker
            for idx, entry in entries:
                # Check for stop request
                if should_stop_callback():
                    print("Generation stopped by user")
                    return
                # Skip already generated sentences if is_continue is True
                if is_continue and entry['generated']:
                    continue
                
                sentence = entry['sentence']
                audio_path = self.generate_audio_proxy(sentence, speaker_settings, s2s_validated)

                if audio_path:
                    new_audio_path = os.path.join(directory_path, f"audio_{idx}.wav")
                    shutil.move(audio_path, new_audio_path)
                    self.text_audio_map[idx]['audio_path'] = new_audio_path
                    self.text_audio_map[idx]['generated'] = True
                    generated_count += 1
                    self.save_text_audio_map(directory_path)
                    sentence_generated_callback(int(idx), sentence)

                # Calculate progress and report
                progress_percentage = int((generated_count / total_sentences) * 100)
                report_progress_callback(progress_percentage)

    def generate_audio_proxy(self, sentence, voice_parameters, s2s_validated):
        # print(voice_parameters)
        tts_engine_name = voice_parameters.get('tts_engine', 'pyttsx3')
        s2s_engine_name = voice_parameters.get('s2s_engine', None)
        

        # Generate a unique temporary file name
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_path = tmp_file.name

        # Now call tts_engines.generate_audio(self.tts_engine, sentence, voice_parameters, tts_engine_name, audio_path)
        success = tts_engines.generate_audio(self.tts_engine, sentence, voice_parameters, tts_engine_name, audio_path)

        if not success:
            return None

        if s2s_validated:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_s2s_file:
                s2s_audio_path = tmp_s2s_file.name
            s2s_engines.process_audio(self.s2s_engine, s2s_engine_name=s2s_engine_name, input_audio_path=audio_path, output_audio_path=s2s_audio_path, parameters=voice_parameters)
            return s2s_audio_path
        else:
            return audio_path

    def execute_subprocess(self, cmd):
        from subprocess import Popen, PIPE, CalledProcessError

        with Popen(cmd, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
            for line in p.stdout:
                print(line, end='')  # process line here

        if p.returncode != 0:
            raise CalledProcessError(p.returncode, p.args)
        

    def export_audiobook(self, directory_path, pause_duration):
        dir_name = os.path.basename(directory_path)
        idx = 0

        # Ensure 'exported_audiobooks' directory exists
        exported_dir = os.path.join(directory_path, "exported_audiobooks")
        if not os.path.exists(exported_dir):
            os.makedirs(exported_dir)

        # Load the JSON file
        audio_map_path = os.path.join(directory_path, 'text_audio_map.json')
        if not os.path.exists(audio_map_path):
            raise FileNotFoundError("The selected directory is not a valid Audiobook Directory.")

        with open(audio_map_path, 'r', encoding='utf-8') as file:
            text_audio_map = json.load(file)

        # Sort the keys (converted to int), then get the corresponding audio paths
        sorted_audio_paths = [text_audio_map[key]['audio_path'] for key in sorted(text_audio_map, key=lambda k: int(k))]

        # Create a silent audio segment for the pause duration
        silence_concat_command = ""
        if pause_duration > 0:
            pause_length = pause_duration * 1000  # convert to milliseconds
            silence = AudioSegment.silent(duration=pause_length)
            silence_path = os.path.join(directory_path, "silence.wav")
            silence.export(silence_path, format="wav")
            silence_concat_command = f"file {os.path.basename(silence_path)}\n"

        # Create a file list for ffmpeg concat demuxer
        first = True
        file_list_path = os.path.join(directory_path, 'file_list.txt')
        with open(file_list_path, 'w') as file:
            for sap in sorted_audio_paths:
                if first:
                    first = False
                else:
                    file.write(silence_concat_command)
                file.write(f"file {os.path.basename(sap)}\n")

        # Find a suitable audio file name with an incrementing suffix
        while True:
            new_audiobook_name = f"{dir_name}_audiobook_{idx}.mp3"
            new_audiobook_path = os.path.join(exported_dir, new_audiobook_name)
            if not os.path.exists(new_audiobook_path):
                break  # Exit the loop once a suitable name is found
            idx += 1

        self.execute_subprocess([AudioSegment.silent(0).ffmpeg, '-f', 'concat', '-safe', '0', '-i', file_list_path, new_audiobook_path])



        print(f"Combined audiobook saved in {new_audiobook_name}")
        return new_audiobook_name


    def update_audiobook(self, directory_path, new_sentences_list):
        audio_map_path = os.path.join(directory_path, 'text_audio_map.json')
        if not os.path.exists(audio_map_path):
            raise FileNotFoundError("The selected directory is not a valid Audiobook Directory.")

        # Load existing text_audio_map
        with open(audio_map_path, 'r', encoding='utf-8') as file:
            text_audio_map = json.load(file)

        # Create reverse map to handle duplicate sentences
        reverse_map = {}
        for idx, item in text_audio_map.items():
            sentence = item['sentence']
            reverse_map.setdefault(sentence, []).append(idx)

        new_text_audio_map = {}
        deleted_indices = set(text_audio_map.keys())
        sentence_counts = {}

        # Collect rename operations
        rename_operations = {}

        for new_idx, sentence in enumerate(new_sentences_list):
            sentence_counts[sentence] = sentence_counts.get(sentence, 0) + 1
            count = sentence_counts[sentence]

            if sentence in reverse_map and len(reverse_map[sentence]) >= count:
                # Existing sentence (consider duplicates)
                old_idx = reverse_map[sentence][count - 1]
                old_item = text_audio_map[old_idx]
                old_audio_path = old_item['audio_path']

                # Extract the basename of the audio file
                old_audio_filename = os.path.basename(old_audio_path)
                old_audio_full_path = os.path.join(directory_path, old_audio_filename)

                # Remove old index from deleted_indices
                deleted_indices.discard(old_idx)

                # Update the item with new index
                new_audio_filename = f"audio_{new_idx}.wav"
                new_audio_full_path = os.path.join(directory_path, new_audio_filename)

                # Update the audio_path in the item
                old_item['audio_path'] = new_audio_full_path  # Store only the filename

                new_text_audio_map[str(new_idx)] = old_item

                # Check if renaming is needed
                if str(new_idx) != old_idx and old_audio_filename:
                    # Record the rename operation
                    rename_operations[old_audio_full_path] = new_audio_full_path
            else:
                # New sentence
                generated = False
                new_audio_filename = ""
                new_text_audio_map[str(new_idx)] = {
                    "sentence": sentence,
                    "audio_path": new_audio_filename,
                    "generated": generated,
                    "speaker_id": 1  # Default speaker
                }

        # Handle deleted sentences and their audio files
        for old_idx in deleted_indices:
            old_audio_path = text_audio_map[old_idx]['audio_path']
            if old_audio_path:
                old_audio_filename = os.path.basename(old_audio_path)
                old_audio_full_path = os.path.join(directory_path, old_audio_filename)
                if os.path.exists(old_audio_full_path):
                    os.remove(old_audio_full_path)  # Delete the audio file
                else:
                    print(f"Audio file to delete not found: {old_audio_full_path}")

        # Now perform the renaming operations without overwriting files

        # Step 1: Rename all source files to temporary files
        temp_files = {}
        for src, dst in rename_operations.items():
            if os.path.exists(src):
                temp_src = src + '.tmp'
                os.rename(src, temp_src)
                temp_files[temp_src] = dst
            else:
                print(f"Warning: Source file '{src}' does not exist.")

        # Step 2: Rename all temporary files to their final destinations
        for temp_src, dst in temp_files.items():
            if os.path.exists(dst):
                os.remove(dst)  # Remove existing file to prevent conflicts
            os.rename(temp_src, dst)

        self.text_audio_map = new_text_audio_map
        self.save_text_audio_map(directory_path)




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


    def save_generation_settings(self, directory_path, speakers=None):
        generation_settings = {}
        if speakers is None:
            speakers = self.speakers
        
        # Convert QColor or Qt.GlobalColor to hex string
        for speaker in speakers.values():
            color = speaker.get('color', '#b0b0b0')
            
            if isinstance(color, QColor):
                # Convert QColor to hex string
                speaker['color'] = color.name()
            elif color == Qt.gray:  # Compare directly with Qt.GlobalColor (integer enum value)
                # Convert Qt.GlobalColor (integer) to QColor and then to hex string
                speaker['color'] = QColor(color).name()
            elif isinstance(color, str):
                # If it's already a string (likely a hex code), do nothing
                pass
            else:
                # If we encounter an unsupported color type, raise an error
                raise TypeError(f"Unsupported color type: {type(color)} for speaker {speaker}, value: {color}")
        
        generation_settings['speakers'] = speakers
        generation_settings_path = os.path.join(directory_path, "generation_settings.json")
        
        # Replace "Default" or "None" strings with None
        self.replace_default_with_none(generation_settings)

        # Save the settings to a JSON file
        self.save_json(generation_settings_path, generation_settings)

        
    def save_temp_generation_settings(self, speakers=None):
        generation_settings = {}
        if speakers is None:
            speakers = self.speakers
        # Convert QColor or Qt.GlobalColor to hex string
        for speaker in speakers.values():
            color = speaker.get('color', '#b0b0b0')
            
            if isinstance(color, QColor):
                # Convert QColor to hex string
                speaker['color'] = color.name()
            elif color == Qt.gray:  # Compare directly with Qt.GlobalColor (integer enum value)
                # Convert Qt.GlobalColor (integer) to QColor and then to hex string
                speaker['color'] = QColor(color).name()
            elif isinstance(color, str):
                # If it's already a string (likely a hex code), do nothing
                pass
            else:
                # If we encounter an unsupported color type, raise an error
                raise TypeError(f"Unsupported color type: {type(color)} for speaker {speaker}, value: {color}")
        
        generation_settings['speakers'] = speakers
        temp_settings_path = os.path.join('temp', "generation_settings.json")
        if not os.path.exists('temp'):
            os.makedirs('temp')
            
        # Replace "Default" or "None" strings with None
        self.replace_default_with_none(generation_settings)
        
        self.save_json(temp_settings_path, generation_settings)
        
    def reset(self):
        self.text_audio_map.clear()
        self.settings.clear()
        self.current_sentence_idx = 0
        self.speakers = {
            1: {'name': 'Narrator', 'color': '#FFFFFF', 'settings': {}}
        }
        self.current_tts_engine_name = None
        self.current_speaker_id = None
        self.current_voice_parameters = None
        self.tts_engine = None
        self.filepath = None

    def load_generation_settings(self, directory_path):
        generation_settings_path = os.path.join(directory_path, "generation_settings.json")
        if os.path.exists(generation_settings_path):
            settings = self.load_json(generation_settings_path)
            # Load speakers
            self.speakers = settings.get('speakers', {})
            # Convert keys to integers
            self.speakers = {int(k): v for k, v in self.speakers.items()}
            # Convert color strings back to QColor
            for speaker in self.speakers.values():
                color = speaker.get('color', '#FFFFFF')
                if isinstance(color, str):
                    speaker['color'] = QColor(color)  # Convert hex string back to QColor
            # print(self.speakers)
            return settings
        else:
            return {}

    def get_s2s_engines(self):
        s2s_config = self.load_config(os.path.join('configs', 's2s_config.json'))
        return [engine['name'] for engine in s2s_config.get('s2s_engines', [])]



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
        
    def replace_default_with_none(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.lower() in ['default', 'none']:
                    data[key] = None
                elif isinstance(value, (dict, list)):
                    self.replace_default_with_none(value)
        elif isinstance(data, list):
            for i in range(len(data)):
                value = data[i]
                if isinstance(value, str) and value.lower() in ['default', 'none']:
                    data[i] = None
                elif isinstance(value, (dict, list)):
                    self.replace_default_with_none(value)

