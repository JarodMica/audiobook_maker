> **Project is currently on hold as of 12/20/2023, but this is one I'll be coming back to in a little bit.**

# Audiobook Maker
This repo utilizes SOTA AI voice generation tools such as Tortoise and RVC to generate the audio required to make an audiobook.  To my knowledge, Tortoise and RVC combined replicates speech in a way that is currently unparalleled to anything else that exists out there that is open-sourced and able to be ran locally. *Eleven labs is absolutely fantastic... one of the best IMO, but it's not "free" and it's not open-source*

There are two ways to install this, via Package or Manually.  If you don't have any 

## Features:
:heavy_check_mark: Sentence generation using Tortoise -> RVC

:heavy_check_mark: RVC AI Voice model compatibility (V1 & V2 as well as 40k & 48k trained models)

:heavy_check_mark: Generation of an entire text file with some basic sentence parsers and sorters

:heavy_check_mark: Selectively playback sentences by clicking and choosing them

:heavy_check_mark: Selectively regenerate audio for sentences by clicking and choosing them

:heavy_check_mark: Progress saving and continuing for audiobook generation in case of a crash or want to continue later

:heavy_check_mark: Audiobook loading from previous generations

:heavy_check_mark: Export of Audiobooks to a single wave file

:heavy_check_mark: Audiobook can be updated with a new text file in case sentences need to be changed or order adjusted

## To-do:
- [ ] Add additional languages (limited to only English ATM)SS
- [ ] Add an option to convert audiobook to another voice 
- [ ] Add a stop generation button
- [ ] Add a Timer
- [ ] Add more advanced playback and regeneration tools
    - [ ] Highlight sentences for generation later (will need to do some type of edit to the json structure so that even if you close out, they are still highlighted)
    - [ ] Find a way to do "multiple speakers" for dialogue in the book (might involve a new tab where users can select sentences to regenerate)
    - [ ] Auto sentence regeneration and comparison using whisper (https://github.com/maxbachmann/RapidFuzz/) 
    - [ ] Add a toggleable option for using rvc conversion


## Prerequisites:
- **NVidia GPU:** I say this is a requirement as I've only developed testing with Nvidia.  The lowest I've tested is an RTX 3060 12B which is more than sufficient, but I reckon that 10 & 20 series cards should still be fine as well.
    - I don't have MAC or AMD so it would be a lot of guess-work for me to get this going and emulation won't work.
- CUDA 11.8
    - https://developer.nvidia.com/cuda-11-8-0-download-archive
    - I believe even if you have CUDA 12.1, it might still be fine as long as you get the correct pytorch version 
- Python 3.10: https://www.python.org/downloads/release/python-31011/ 
- git: https://git-scm.com/downloads 
- mrq's Tortoise Fork: https://git.ecker.tech/mrq/ai-voice-cloning/wiki/Installation
    - YouTube video guide: https://youtu.be/6sTsqSQYIzs?si=0NYteSephE1ePiFg
    - Audio generation MUST be working as we will be calling tortoise via an API
- 7zip extractor
    - Download from here: https://www.7-zip.org/

## Package Installation
**Make sure you have Tortoise installed and working as stated in prerequisites**

1. Head over to the releases tab and download the audiobook maker 7zip folder from my HuggingFace Repo: 

2. Unzip using 7zip (or your preferred 7zip unpacker)

3. Inside of the audiobook maker folder, right click and edit tort.yaml with a voice that is working in Tortoise TTS (more details in video)

4. Run the ```start_package.bat```

5. Before generating an audio, make sure that Tortoise TTS is also running in the background so that it can generate audio.

## Manual Installation:

**Make sure you have Tortoise installed and working as stated in prerequisites**

1. Open a powershell/cmd window, clone, and then cd into the repo:
```
git clone https://github.com/JarodMica/audiobook_maker.git
cd audiobook_maker
```

2. Download and extract rvc to the audiobook_maker folder:
    - Link: https://huggingface.co/Jmica/rvc/resolve/main/rvc_lightweight.7z
        - Extract and double-click into ```rvc_lightweight```, and then copy the ```rvc``` folder into the ```audiobook_maker``` folder 
        - It should look like ```audiobook_maker/rvc``` and NOT like ```audiobook_maker\rvc_lightweight```
    - You can delete rvc_lightweight.7z and the folder once the copy is finished

3. Set-up and activate virtual environment
```
python -m venv venv
venv\Scripts\activate
```
4. Install pytorch using command below (recommended) or get from https://pytorch.org/get-started/locally/:

```pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121```

5. Install requirements:

```pip install -r requirements.txt```

```pip install -r rvc/requirements.txt``` (if you get an error here, check to make sure you copied the rvc folder correctly)

```pip install https://huggingface.co/Jmica/rvc/resolve/main/fairseq-0.12.2-cp310-cp310-win_amd64.whl```

```pip install git+https://github.com/JarodMica/rvc-tts-pipeline.git@lightweight#egg=rvc_tts_pipe```

```pip install git+https://github.com/JarodMica/tortoise_api.git```

6. Download and install ffmpeg: https://ffmpeg.org/download.html
    - Place ffmpeg.exe and ffprobe.exe inside of audiobook_maker OR make sure they are in your environment path variable

7. Place whatever RVC AI voices (.pth) you want into the ```voice_models``` directory and indexes into ```voice_indexes```

## Acknowledgements
I am able to build these tools thanks to all of the fantastic open source repos out there, borrowing from different projects to get this all frankensteined and hashed together.  Without these, it wouldn't be possible for me to have gotten the functionality needed to create such a fantastic tool:
- mrq's AI Voice Cloning / Tortoise branch: https://git.ecker.tech/mrq/ai-voice-cloning
- Retrieval Based Voice Conversion: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI
- OpenAI's ChatGPT for rapid development and prototyping, speeding up implementation and brainstorming by tenfolds
