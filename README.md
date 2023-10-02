# Audiobook Maker
This repo utilizes SOTA AI voice generation tools such as Tortoise and RVC to generate the audio required to make an audiobook.  To my knowledge, Tortoise and RVC combined replicates speech in a way that is currently unparalleled to anything else that exists out there that is open-sourced and able to be ran locally. *Eleven labs is absolutely fantastic... one of the best IMO, but it's not "free" and it's not open-source*

To get this going is relatively installation heavy, but at this stage, I lack the proper skills and knowledge needed to get this packaged up and working in a way that is simply a one folder install.

## Features:
:heavy_check_mark: Sentence generation using Tortoise -> RVC

:heavy_check_mark: RVC AI Voice model compatibility (V1 & V2 as well as 40k & 48k trained models)

:heavy_check_mark: Generation of an entire text file with some basic sentence parsers and sorters

:heavy_check_mark: Selectively playback sentences by clicking and choosing them

:heavy_check_mark: Selectively regenerate audio for sentences by clicking and choosing them

:heavy_check_mark: Progress saving and continuing for audiobook generation in case of a crash or want to continue later

:heavy_check_mark: Audiobook loading from previous generations

:heavy_check_mark: Export of Audiobooks to a single wave file

## To-do:
- [ ] Add additional languages (limited to only English ATM)
- [ ] Simpler installation, making it into release
- [ ] Need to add a "modify audiobook text" so that you could add more sentences to the end of a file and continue generating
- [ ] Add an option to convert audiobook to another voice 

## Prerequisites:
- **NVidia GPU:** I say this is a requirement as I've only developed testing with Nvidia.  The lowest I've tested is an RTX 3060 12B which is more than sufficient, so I reckon that 10 & 20 series cards should still be fine as well.
    - I don't have MAC or AMD so it would be a lot of guess-work for me to get this going and emulation won't work.
- CUDA 11.7
    - I believe even if you have CUDA 12.1, it might still be fine as long as you get the correct pytorch version 
- Python 3.9/3.10: https://www.python.org/downloads/release/python-31011/ 
- git: https://git-scm.com/downloads 
- mrq's Tortoise Fork: https://git.ecker.tech/mrq/ai-voice-cloning/wiki/Installation
    - YouTube video guide: https://youtu.be/6sTsqSQYIzs?si=0NYteSephE1ePiFg
    - Audio generation MUST be working as we will be calling tortoise via an API

## Installation:
**NEEDED BUT NOT MENTIONED IN VIDEO**

Microsoft c++ build tools needs to be installed on your PC or else you will run into issues when installing the rvc package. This tutorial is quick and shows how it needs to get done: https://youtu.be/rcI1_e38BWs?si=tlbs5xniFo1UOVVU

1. Open a powershell/cmd window, clone, and then cd into the repo:
```
git clone https://github.com/JarodMica/audiobook_maker.git
cd audiobook_maker
```
2. Set-up and activate virtual environment
```
python -m venv venv
venv\Scripts\activate
```
3. Install pytorch from https://pytorch.org/get-started/locally/ or use the command below:

```pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117```

4. Install requirements:

```pip install -r requirements.txt```

```pip install -e git+https://github.com/JarodMica/rvc.git#egg=rvc```

```pip install -e git+https://github.com/JarodMica/rvc-tts-pipeline.git#egg=rvc_tts_pipe```

5. Download and place rmvpe.pt and hubert_base.pt in audiobook_maker
    - You can get them at my huggingface here: https://huggingface.co/Jmica/rvc_base_models/tree/main
    - OR you can get them from the RVC huggingface: https://huggingface.co/lj1995/VoiceConversionWebUI/tree/main
6. Download and install ffmpeg: https://ffmpeg.org/download.html
    - Place ffmpeg.exe and ffprobe.exe inside of audiobook_maker OR make sure they are in your environment path variable
7. Place whatever RVC AI voices (.pth) files into the voice_models directory.
    - Index files are currently not supportedm, but I will be building this into the GUI eventually

## Acknowledgements
I am able to build these tools thanks to all of the fantastic open source repos out there, borrowing from different projects to get this all frankensteined and hashed together.  Without these, it wouldn't be possible for me to have gotten the functionality needed to create such a fantastic tool:
- mrq's AI Voice Cloning / Tortoise branch: https://git.ecker.tech/mrq/ai-voice-cloning
- Retrieval Based Voice Conversion: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI

And of course, this goes without saying, but ChatGPT has guided and helped me form my ideas into implementation.  The amount of time saved from using such a tool is unparalleled to any tool that I've ever used up until this point and the ability of it to turn sheer ideas into reality is absolutely mind boggling.  
