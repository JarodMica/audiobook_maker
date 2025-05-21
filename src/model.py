# model.py 

import os
import json
import shutil
from pydub import AudioSegment
import pyttsx3
import re
import subprocess
import tempfile

import tts_engines
import s2s_engines

from collections import defaultdict
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from subprocess import Popen, PIPE, CalledProcessError

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
    def assign_speaker_to_sentence(self, idx, speaker_id):
        idx_str = str(idx)
        if idx_str in self.text_audio_map:
            self.text_audio_map[idx_str]['speaker_id'] = speaker_id
    def change_regen_state(self, idx, state):
        idx_str = str(idx)
        if idx_str in self.text_audio_map:
            self.text_audio_map[idx_str]["regen"] = state
    def clear_background_image(self):
        self.save_settings(background_image=None) 
    def create_audio_text_map(self, directory_path, sentences_list):
        new_text_audio_map = {}
        for idx, sentence in enumerate(sentences_list):
            generated = False
            audio_path = ""
            new_text_audio_map[str(idx)] = self.default_text_audio_map_format(sentence=sentence, audio_path=audio_path, generated=generated)
        self.text_audio_map = new_text_audio_map
    def create_book_text_file(self, text_file_destination):
        file_name = "book_text.txt"
        full_path = os.path.join(text_file_destination, file_name)
        with open(full_path, "w", encoding="utf-8") as f:
            for idx in self.text_audio_map:
                text = self.text_audio_map[idx]["sentence"]
                f.write(text + "\n\n")
    def delete_sentences(self, rows_list):
        sorted_items = sorted(self.text_audio_map.items(), key=lambda x: int(x[0]))
        filtered_items = [(k, v) for k, v in sorted_items if int(k) not in rows_list]
        adjusted_items = [(str(i), v) for i, (_, v) in enumerate(filtered_items, start=0)]
        adjusted_dict = {k: v for k, v in adjusted_items}
        self.text_audio_map = adjusted_dict
        # Rename audio files on disk to match new indices
        rename_map = {}
        for idx_str, entry in self.text_audio_map.items():
            old_path = entry.get('audio_path')
            if old_path and os.path.exists(old_path):
                dirpath = os.path.dirname(old_path)
                temp_path = old_path + '.tmp'
                os.rename(old_path, temp_path)
                rename_map[temp_path] = os.path.join(dirpath, f'audio_{idx_str}.wav')
        for temp_path, new_path in rename_map.items():
            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(temp_path, new_path)
            new_idx_str = os.path.splitext(os.path.basename(new_path))[0].split('_')[-1]
            self.text_audio_map[new_idx_str]['audio_path'] = new_path
    def default_text_audio_map_format(self, **kwargs):
        text_audio_map = {
            "sentence": kwargs.get("sentence"),
            "audio_path": kwargs.get("audio_path"),
            "generated": kwargs.get("generated"),
            "speaker_id": 1,
            "regen" : False
        }
        return text_audio_map
    def execute_subprocess(self, cmd):
        with Popen(cmd, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
            for line in p.stdout:
                print(line, end='')
        if p.returncode != 0:
            raise CalledProcessError(p.returncode, p.args)
    def export_audiobook(self, directory_path, pause_duration):
        dir_name = os.path.basename(directory_path)
        idx = 0
        exported_dir = os.path.join(directory_path, "exported_audiobooks")
        if not os.path.exists(exported_dir):
            os.makedirs(exported_dir)
        audio_map_path = os.path.join(directory_path, 'text_audio_map.json')
        if not os.path.exists(audio_map_path):
            raise FileNotFoundError("The selected directory is not a valid Audiobook Directory.")
        with open(audio_map_path, 'r', encoding='utf-8') as file:
            text_audio_map = json.load(file)
        sorted_audio_paths = [text_audio_map[key]['audio_path'] for key in sorted(text_audio_map, key=lambda k: int(k))]
        def probe_audio_properties(file_path):
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=sample_rate,channels,bits_per_sample',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"ffprobe error: {result.stderr}")
            lines = result.stdout.strip().split('\n')
            if len(lines) != 3:
                raise ValueError("ffprobe did not return sample_rate, channels, and bits_per_sample")
            sample_rate, channels, bits_per_sample = lines
            return int(sample_rate), int(channels), int(bits_per_sample)
        silence_concat_command = ""
        if pause_duration > 0:
            pause_length = pause_duration * 1000
            if not sorted_audio_paths:
                raise ValueError("No audio files found to determine silence properties.")
            first_audio_path = sorted_audio_paths[0]
            sample_rate, channels, bits_per_sample = probe_audio_properties(first_audio_path)
            silence = AudioSegment.silent(duration=pause_length, frame_rate=sample_rate)
            silence = silence.set_channels(channels)
            silence = silence.set_sample_width(bits_per_sample // 8)
            silence_path = os.path.join(directory_path, "silence.wav")
            silence.export(silence_path, format="wav")
            silence_concat_command = f"file '{os.path.basename(silence_path)}'\n"
        first = True
        file_list_path = os.path.join(directory_path, 'file_list.txt')
        with open(file_list_path, 'w') as file:
            for sap in sorted_audio_paths:
                if first:
                    first = False
                else:
                    file.write(silence_concat_command)
                file.write(f"file {os.path.basename(sap)}\n")
        while True:
            new_audiobook_name = f"{dir_name}_audiobook_{idx}.mp3"
            new_audiobook_path = os.path.join(exported_dir, new_audiobook_name)
            if not os.path.exists(new_audiobook_path):
                break
            idx += 1
        self.execute_subprocess([AudioSegment.silent(0).ffmpeg, '-f', 'concat', '-safe', '0', '-i', file_list_path, new_audiobook_path])
        print(f"Combined audiobook saved in {new_audiobook_name}")
        return new_audiobook_name
    def filter_paragraph(self, paragraph):
        sentences = []
        for line in paragraph.split('\n'):
            line = line.strip()
            if line and any(c.isalpha() for c in line):
                sentences.append(line)
        return sentences
    # def filter_paragraph(self, paragraph):
    #     lines = paragraph.strip().split('\n')
    #     filtered_list = []
    #     i = 0
    #     while i < len(lines):
    #         split_sentences = lines[i].split('. ')
    #         for part_sentence in split_sentences:
    #             if not part_sentence:
    #                 continue
    #             line = part_sentence.strip()
    #             while line.endswith(",") and (i + 1) < len(lines):
    #                 i += 1
    #                 line += " " + lines[i].split('. ')[0].strip()
    #             line = re.sub(r'\[|\]', '', line).strip()
    #             if line and any(c.isalpha() for c in line):
    #                 filtered_list.append(line)
    #         i += 1
    #     return filtered_list
    def generate_audio_for_sentence_threaded(self, directory_path, is_continue, is_regen_only, report_progress_callback, sentence_generated_callback, should_stop_callback=None):
        self.load_generation_settings(directory_path)
        self.load_text_audio_map(directory_path)
        if is_regen_only:
            total_sentences = sum(1 for entry in self.text_audio_map.values() if entry['regen'])
            if total_sentences == 0:
                return
        else:
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
        for speaker_id, entries in sentences_by_speaker.items():
            speaker = self.speakers.get(speaker_id, {})
            speaker_settings = speaker.get('settings', {})
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
            for idx, entry in entries:
                if should_stop_callback():
                    print("Generation stopped by user")
                    return
                if is_continue and entry['generated']:
                    continue
                if is_regen_only:
                    if entry['regen']:
                        pass
                    else:
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
                progress_percentage = int((generated_count / total_sentences) * 100)
                report_progress_callback(progress_percentage)
    def generate_audio_proxy(self, sentence, voice_parameters, s2s_validated):
        tts_engine_name = voice_parameters.get('tts_engine', 'pyttsx3')
        s2s_engine_name = voice_parameters.get('s2s_engine', None)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_path = tmp_file.name
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
    def get_map_keys_and_values(self, idx_str):
        item = self.text_audio_map[idx_str]
        row_position = int(idx_str)
        sentence = item['sentence']
        speaker_id = item.get('speaker_id', 1)
        speaker_name = self.get_speaker_name(speaker_id)
        regen_state = item['regen']
        return sentence, row_position, speaker_id, speaker_name, regen_state
    def get_s2s_engines(self):
        s2s_config = self.load_config(os.path.join('configs', 's2s_config.json'))
        return [engine['name'] for engine in s2s_config.get('s2s_engines', [])]
    def get_speaker_name(self, speaker_id):
        speaker_name = self.speakers[speaker_id]['name']
        return speaker_name
    def get_tts_engines(self):
        tts_config = self.load_config(os.path.join('configs', 'tts_config.json'))
        return [engine['name'] for engine in tts_config.get('tts_engines', [])]
    def get_voice_indexes(self):
        if os.path.exists(self.index_folder_path) and os.path.isdir(self.index_folder_path):
            voice_index_files = [file for file in os.listdir(self.index_folder_path) if file.endswith(".index")]
            return voice_index_files
        return []
    def get_voice_models(self):
        if os.path.exists(self.voice_folder_path) and os.path.isdir(self.voice_folder_path):
            voice_model_files = [file for file in os.listdir(self.voice_folder_path) if file.endswith(".pth")]
            return voice_model_files
        return []
    def load_config(self, config_path):
        if not os.path.exists(config_path):
            return {}
        with open(config_path, 'r') as f:
            return json.load(f)
    def load_generation_settings(self, directory_path):
        generation_settings_path = os.path.join(directory_path, "generation_settings.json")
        if os.path.exists(generation_settings_path):
            settings = self.load_json(generation_settings_path)
            self.speakers = settings.get('speakers', {})
            self.speakers = {int(k): v for k, v in self.speakers.items()}
            for speaker in self.speakers.values():
                color = speaker.get('color', '#FFFFFF')
                if isinstance(color, str):
                    speaker['color'] = QColor(color)
            return settings
        else:
            return {}
    def load_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    def load_selected_s2s_engine(self, chosen_s2s_engine, speaker_id, **kwargs):
        if (self.current_s2s_engine_name == chosen_s2s_engine and
            self.current_s2s_speaker_id == speaker_id and
            self.current_s2s_parameters == kwargs):
            return True
        else:
            try:
                self.s2s_engine = s2s_engines.load_s2s_engine(chosen_s2s_engine, **kwargs)
                if self.s2s_engine == None:
                    return False
                self.current_s2s_engine_name = chosen_s2s_engine
                self.current_s2s_speaker_id = speaker_id
                self.current_s2s_parameters = kwargs
                return True
            except Exception as e:
                print(f"Failed to load s2s engine '{chosen_s2s_engine}': {e}")
                return False
    def load_selected_tts_engine(self, chosen_tts_engine, speaker_id, **kwargs):
        if (self.current_tts_engine_name == chosen_tts_engine and
            self.current_speaker_id == speaker_id and
            self.current_voice_parameters == kwargs):
            return self.tts_engine
        else:
            self.tts_engine = tts_engines.load_tts_engine(chosen_tts_engine, **kwargs)
            self.current_tts_engine_name = chosen_tts_engine
            self.current_speaker_id = speaker_id
            self.current_voice_parameters = kwargs
            return self.tts_engine
    def load_sentences(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            paragraphs = content.split('\n\n')
            filtered_sentences = []
            for paragraph in paragraphs:
                filtered_list = self.filter_paragraph(paragraph)
                filtered_sentences.extend(filtered_list)
        return filtered_sentences
    def load_settings(self):
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as json_file:
                self.settings = json.load(json_file)
                return self.settings
        return {}
    def load_text_audio_map(self, directory_path):
        map_file_path = os.path.join(directory_path, "text_audio_map.json")
        if not os.path.exists(map_file_path):
            raise FileNotFoundError("The selected directory is not a valid Audiobook Directory.")
        with open(map_file_path, 'r', encoding="utf-8") as map_file:
            self.text_audio_map = json.load(map_file)
        return self.text_audio_map
        
    def paragraph_to_sentence(self,paragraph) -> list:
        #This removes annoying pauses, and things like "greater than..." because a book
        #formatted computer text with '>' for example.
        paragraph = re.sub('\n|-', ' ', re.sub('\[|\]|\*|\\|\<|\>|_|\"|\“|\”', '', paragraph))
        paragraph = re.sub('…', '-', paragraph)
        
        # Substitutions for some abbreviations, can just be in rplwords, but these are common
        paragraph = paragraph.replace('Mr.','Mister')
        paragraph = paragraph.replace('Mrs.','Misses')
        paragraph = paragraph.replace('Ms.','Miz')
        paragraph = paragraph.replace('Dr.','Doctor')
        #add space before period, to improve end of sentence audio for tortoise for example.
        #removed space after period
        #paragraph = paragraph.replace(r'. ', ' .*%')
        paragraph = paragraph.replace(r'.', ' .*%')
        
        #This removes excess spaces.  
        #These occur with indented paragraphs without periods.
        #Included poems for example.
        paragraph = paragraph.replace(r'     ', ' ')
        paragraph = paragraph.replace(r'    ', ' ')
        paragraph = paragraph.replace(r'   ', ' ')
        paragraph = paragraph.replace(r'  ', ' ')

        sentence_list = [s.strip() for s in paragraph.split('*%') if (s.strip()!='.' and s.strip()!='')]
        return sentence_list
    def process_upload_items(self, mode, save_items):
        for item in save_items:
            if item.get('name', None):
                name = item['name']
        for file_to_save in save_items:
            if file_to_save.get('name', None):
                continue
            type = file_to_save['type']
            if type == 'file':
                source_path = file_to_save['source_path']
                base_target_path = file_to_save['target_path']
                ext = os.path.splitext(source_path)[1]
                new_name = f"{name}{ext}"
                if file_to_save['save_format'] == 'folder':
                    target_path = os.path.join(base_target_path, name, new_name)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                else:
                    target_path = os.path.join(base_target_path, new_name)
                if os.path.exists(target_path):
                    raise Exception(f"The file '{target_path}' already exists, please delete it before uploading a new voice.")
                shutil.copy2(source_path, target_path)
            elif type == 'text':
                source_text = file_to_save['source_text']
                base_target_path = file_to_save['target_path']
                target_path = os.path.join(base_target_path, name, f"{name}.txt")
                if os.path.exists(target_path):
                    raise Exception(f"The file '{target_path}' already exists, please delete it before uploading a new voice.")
                with open(target_path, 'w') as f:
                    f.write(source_text)
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
                    
    def replace_words_from_list(self, replacement_file_path, extra):
        with open(replacement_file_path, 'r', encoding='utf-8') as f:
            replacements = json.load(f)

        for key, value in self.text_audio_map.items():
            sentence = value['sentence']

            #This needed to happen before the word replacement
            if extra:
                #so things like Mr becomes Mister, since period is required.
                if sentence[-1] != ".":
                    sentence =  sentence + "."
                
                sentence_list = self.paragraph_to_sentence(sentence)
                sentence = ' '.join(sentence_list)

            for _, replacement_data in replacements.items():
                orig_word = replacement_data['orig_word']
                replacement_word = replacement_data['replacement_word']
            
                pattern = r"\b{}\b".format(re.escape(orig_word))
                #So sentences with replaced words are regenerated
                if orig_word in sentence:
                    value['regen'] = True  #I like this, but it is required
                    value['generated'] = False
                sentence = re.sub(pattern, replacement_word, sentence)

            value['sentence'] = sentence

    def reset(self):
        self.text_audio_map.clear()
        self.settings.clear()
        self.current_sentence_idx = 0
        self.speakers = {
            "1": {'name': 'Narrator', 'color': '#FFFFFF', 'settings': {}}
        }
        self.current_tts_engine_name = None
        self.current_speaker_id = None
        self.current_voice_parameters = None
        self.tts_engine = None
        self.filepath = None
    def reset_regen_in_text_audio_map(self):
        for idx_str in self.text_audio_map:
            self.text_audio_map[idx_str]["regen"] = False
    def save_generation_settings(self, directory_path, speakers=None):
        generation_settings = {}
        if speakers is None:
            speakers = self.speakers
        for speaker in speakers.values():
            color = speaker.get('color', '#b0b0b0')
            if isinstance(color, QColor):
                speaker['color'] = color.name()
            elif color == Qt.black:
                speaker['color'] = QColor(color).name()
            elif isinstance(color, str):
                pass
            else:
                raise TypeError(f"Unsupported color type: {type(color)} for speaker {speaker}, value: {color}")
        generation_settings['speakers'] = speakers
        generation_settings_path = os.path.join(directory_path, "generation_settings.json")
        self.replace_default_with_none(generation_settings)
        self.save_json(generation_settings_path, generation_settings)
    def save_json(self, file_path, data):
        def default_serializer(obj):
            if isinstance(obj, QColor):
                return obj.name()
            elif isinstance(obj, int):
                return QColor(obj).name()
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4, default=default_serializer)
    def save_settings(self, background_image=None):
        self.settings['background_image'] = background_image
        with open('settings.json', 'w') as json_file:
            json.dump(self.settings, json_file)
    def save_temp_generation_settings(self, speakers=None):
        generation_settings = {}
        if speakers is None:
            speakers = self.speakers
        for speaker in speakers.values():
            color = speaker.get('color', '#b0b0b0')
            if isinstance(color, QColor):
                speaker['color'] = color.name()
            elif color == Qt.black:
                speaker['color'] = QColor(color).name()
            elif isinstance(color, str):
                pass
            else:
                raise TypeError(f"Unsupported color type: {type(color)} for speaker {speaker}, value: {color}")
        generation_settings['speakers'] = speakers
        temp_settings_path = os.path.join('temp', "generation_settings.json")
        if not os.path.exists('temp'):
            os.makedirs('temp')
        self.replace_default_with_none(generation_settings)
        self.save_json(temp_settings_path, generation_settings)
    def save_text_audio_map(self, directory_path):
        map_file_path = os.path.join(directory_path, "text_audio_map.json")
        with open(map_file_path, 'w', encoding="utf-8") as map_file:
            json.dump(self.text_audio_map, map_file, ensure_ascii=False, indent=4)
    def set_background_image(self, file_name):
        if not os.path.exists('image_backgrounds'):
            os.makedirs('image_backgrounds')
        image_name = os.path.basename(file_name)
        destination_path = os.path.join('image_backgrounds', image_name)
        if os.path.abspath(file_name) != os.path.abspath(destination_path):
            shutil.copy2(file_name, destination_path)
        self.save_settings(background_image=destination_path)
        return destination_path
    def update_audiobook(self, directory_path, new_sentences_list):
        audio_map_path = os.path.join(directory_path, 'text_audio_map.json')
        if not os.path.exists(audio_map_path):
            raise FileNotFoundError("The selected directory is not a valid Audiobook Directory.")
        with open(audio_map_path, 'r', encoding='utf-8') as file:
            text_audio_map = json.load(file)
        reverse_map = {}
        for idx, item in text_audio_map.items():
            sentence = item['sentence']
            reverse_map.setdefault(sentence, []).append(idx)
        new_text_audio_map = {}
        deleted_indices = set(text_audio_map.keys())
        sentence_counts = {}
        rename_operations = {}
        for new_idx, sentence in enumerate(new_sentences_list):
            sentence_counts[sentence] = sentence_counts.get(sentence, 0) + 1
            count = sentence_counts[sentence]
            if sentence in reverse_map and len(reverse_map[sentence]) >= count:
                old_idx = reverse_map[sentence][count - 1]
                old_item = text_audio_map[old_idx]
                old_audio_path = old_item['audio_path']
                old_audio_filename = os.path.basename(old_audio_path)
                old_audio_full_path = os.path.join(directory_path, old_audio_filename)
                deleted_indices.discard(old_idx)
                new_audio_filename = f"audio_{new_idx}.wav"
                new_audio_full_path = os.path.join(directory_path, new_audio_filename)
                old_item['audio_path'] = new_audio_full_path
                new_text_audio_map[str(new_idx)] = old_item
                if str(new_idx) != old_idx and old_audio_filename:
                    rename_operations[old_audio_full_path] = new_audio_full_path
            else:
                generated = False
                new_audio_filename = ""
                new_text_audio_map[str(new_idx)] = self.default_text_audio_map_format(sentence=sentence, audio_path=new_audio_filename, generated=generated)
        for old_idx in deleted_indices:
            old_audio_path = text_audio_map[old_idx]['audio_path']
            if old_audio_path:
                old_audio_filename = os.path.basename(old_audio_path)
                old_audio_full_path = os.path.join(directory_path, old_audio_filename)
                if os.path.exists(old_audio_full_path):
                    os.remove(old_audio_full_path)
                else:
                    print(f"Audio file to delete not found: {old_audio_full_path}")
        temp_files = {}
        for src, dst in rename_operations.items():
            if os.path.exists(src):
                temp_src = src + '.tmp'
                os.rename(src, temp_src)
                temp_files[temp_src] = dst
            else:
                print(f"Warning: Source file '{src}' does not exist.")
        for temp_src, dst in temp_files.items():
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(temp_src, dst)
        self.text_audio_map = new_text_audio_map
        self.save_text_audio_map(directory_path)
    def update_sentence_in_text_audio_map(self, idx, new_text):
        idx_str = str(idx)
        if idx_str in self.text_audio_map:
            self.text_audio_map[idx_str]['sentence'] = new_text
            self.text_audio_map[idx_str]["generated"] = False
    def update_speakers(self, speakers):
        self.speakers = speakers
    def update_text_audio_map(self, sentences_list):
        new_text_audio_map = {}
        sentence_to_existing_idx = {item['sentence']: idx for idx, item in self.text_audio_map.items()}
        for idx, sentence in enumerate(sentences_list):
            if sentence in sentence_to_existing_idx:
                existing_idx = sentence_to_existing_idx[sentence]
                item = self.text_audio_map[existing_idx]
                new_text_audio_map[str(idx)] = item
            else:
                generated = False
                audio_path = ""
                new_text_audio_map[str(idx)] = self.default_text_audio_map_format(sentence=sentence, audio_path=audio_path, generated=generated)              
        self.text_audio_map = new_text_audio_map
