# Audiobook Maker v3
This application utilizes open-source deep-learning text-to-speech and speech-to-speech models to create audiobooks.  The main goal of the project is to be able to seamlessly create high-quality audiobooks by using these advancements in machine learning/AI.

It's designed for **Windows,** but pyside6 should be able to run on linux.

## Table of Contents
- [Features](#features)
- [What changed from v1 and v2?](#what-changed-from-v1-and-v2)
  - [As a user?](#as-a-user)
  - [As a developer?](#as-a-developer)
- [Windows Package Installation](#windows-package-installation)
- [Manual Installation Windows 10/11](#manual-installation-windows-1011)
- [Usage](#usage)
- [Acknowledgements](#acknowledgements)

### Install Specific Engines
- [TortoiseTTS Installation](#tortoisetts-installation)
- [StyleTTS 2 Installation](#styletts-2-installation)
- [RVC Installation](#rvc-installation)

## Features
:heavy_check_mark: Multi-speaker generation, allowing you to change who speaks which sentence etc.

:heavy_check_mark: Audio playback of individually generated sentences, or playback all to listen as it generates

:heavy_check_mark: Stopping during generation to pick up later, continuing to continue where you stopped from

:heavy_check_mark: Bulk sentence regeneration and editting in case you want to regenerate audio for a sentence or change which speaker is being used for a sentence

:heavy_check_mark: Reloading previous audiobooks and exporting audiobooks

:heavy_check_mark: Sentence remapping in case you need to update the original text file that was used for generation

:heavy_check_mark: Integration with popular open-source models like TortoiseTTS, RVC, StyleTTS (to be added), and XTTS (to be added)

## What changed from v1 and v2?
### As a user?
The biggest thing would be the ability to use multiple speakers, regenerate in bulk, and to stop during generation.  It still fulfills pretty much the same stuff as before.

### As a developer?
A lot. Pretty much the entire codebase was rewritten with the sole goal of making it **more maintainable and more modular.**  This can be summarized in two points:

1. #### The most important: Completely removed any hardcoded parameters that referenced any TTS or S2S engine (tortoise/rvc)
    This makes it a (relavtive) breeze to add in any new TTS engines or S2S engine. You simply just need to create a configuration for that engine in the configs folder as all widgets in the GUI are created and handled dynamically, define a loading and generation procedure in the s2s or tts engines python file, and it'll work with very little to no issues.  I designed it with the intention so that as long as the engine returns an audio_path back to the `model.py`, it will integrate just fine.  I'll be writing documentation on how to do this so that I don't forget in the future, but it might be useful for anyone who want to fork this repo and build on it.

2. #### Moved over to MVC
    Point 1 wouldn't be as smooth without this. The previous implementation was heavily coupled together in one, ginormous class and that was getting too cramped and too messy to keep up with.  So I moved over to something closer to an MVC framework and separated out the gui into `view.py`, the "brain" and logic into the `controller.py`, and all of the functional code into the `model.py`.  Still messy, but not *as* messy as it would've been if I didn't switch over.

A minor change as well was the migration from pyqt5 --> pyside 6, but that wasn't too big of an issue.  Small peculiar issues here and there, but nothing ground breaking.

I have decided to **NOT** use gradio for this.  The biggest reason being that the previous versions were done in pyqt5.  Another being my concern for limitations on customizability.  I've done a fair share of work in gradio and I don't think that the way I want the audiobook maker to look and feel would be easily achievable by using it. And the last reason being I don't want a web interface or a local web server to be launched (maybe some users would run into issues with this).  However, because I'm not using gradio, this also cannot be used on a cloud computer, so you will need all the hardware on your computer locally.


## Windows Package Installation
Will be available for Youtube Channel Members at the Supporter (Package) level: https://www.youtube.com/channel/UCwNdsF7ZXOlrTKhSoGJPnlQ/join
### Pre-requisites
- NVIDIA GPU with at least 8GB of VRAM (for heavier inference models like Tortoise, 4-6 GB might be possible as we're not training here)

1. Download the zip file provided to you on the members community tab.
2. Unzip the folder
3. Run the `start.bat` file

And that's it! (maybe)

If you run into issues, check your drivers and make sure they're up to date.  If you don't run into issues, I recommend not updating.

## Manual Installation Windows 10/11
### Pre-requistites
- Python 3.11: https://www.python.org/downloads/release/python-3119/
- git: https://git-scm.com/
- vscode (optional): https://code.visualstudio.com/
- ffmpeg: https://www.ffmpeg.org/download.html#build-windows
  - Watch a tutorial here: https://www.youtube.com/watch?v=JR36oH35Fgg&t=159s&ab_channel=Koolac
- NVIDIA GPU with at least 8GB of VRAM (for heavier inference models like Tortoise, 4-6 GB might be possible as we're not training here)
- Install CUDA toolkit, see issue: https://github.com/JarodMica/audiobook_maker/issues/63#issuecomment-2430191713

### GUI Installation
1. Clone the repository and cd into it.
   ```
   git clone https://github.com/JarodMica/audiobook_maker.git
   cd audiobook_maker
   ```
2. Create a venv in python 3.11 and then activate it.  If you can't activate the python venv due to restricted permissions: https://superuser.com/questions/106360/how-to-enable-execution-of-powershell-scripts
   ```
   py -3.11 -m venv venv
   .\venv\Scripts\activate
   ```
3. Install basic requirements to get the GUI opening
   ```
   pip install -r .\requirements.txt
   ```
4. Pull submodules
   ```
   git submodule init
   git submodule update --remote
   ```  
5. Launch the interface
   ```
   python .\src\controller.py
   ```
6. (Optional) I recommend you create a batch script to launch the gui instead of manually doing it each time. Open notepad, throw the code block below into it, name it `start.bat`, and it should be fine.  Make sure your extensions are showing so that it's not `start.bat.txt`
   ```
   call venv\Scripts\activate
   python src\controller.py
   ```
Congrats, the GUI can be launched!  You should see in the errors in the terminal such as `Tortoise not installed` or `RVC not installed`

If you use it like this, you will only be able to use pyttsx3.  To install additional engines, refer to the sections below to get the engines you want installed, I recommend you do all of them.

### Text-to-Speech Engines
#### TortoiseTTS Installation
0. Make sure your venv is still activated, if not, activate it:
   ```
   .\venv\Scripts\activate
   ```
2. Change directory to tortoise submodule, then pull its submodules:
   ```
   cd .\modules\tortoise_tts_api\
   git submodule init
   git submodule update
   ```
3. Install the submodules:
   ```
   pip install modules\tortoise_tts
   pip install modules\dlas
   ```
4. Install the tortoise tts api repo, then cd back to root:
   ```
   pip install .
   cd ..\..
   ```
5. Ensure you have pytorch installed with CUDA enabled [Check Torch Install](#check-torch-install)

#### StyleTTS 2 Installation
0. Make sure your venv is still activated, if not, activate it:
   ```
   .\venv\Scripts\activate
   ```
2. Change directory to styletts submodule, then pull its submodules:
   ```
   cd .\modules\styletts-api\
   git submodule init
   git submodule update
   ```
3. Install the submodules:
   ```
   pip install modules\StyleTTS2
   ```
4. Install the styletts api repo, then cd back to root:
   ```
   pip install .
   cd ..\..
   ```
5. Install monotonic align:
```
pip install git+https://github.com/resemble-ai/monotonic_align.git@78b985be210a03d08bc3acc01c4df0442105366f
```
6. Ensure you have pytorch installed with CUDA enabled [Check Torch Install](#check-torch-install)


### Speech-to-Speech Engines
#### RVC Installation
0. Make sure your venv is still activated, if not, activate it:
   ```
   .\venv\Scripts\activate
   ```
1. Install fairseq as a wheels file.  Download it from this link here https://huggingface.co/Jmica/rvc/resolve/main/fairseq-0.12.4-cp311-cp311-win_amd64.whl?download=true and place it in the `audiobook_maker` :
   ```
   pip install .\fairseq-0.12.4-cp311-cp311-win_amd64.whl
   ```
    It's done this way due to issues with fairseq on python 3.11 and above so I've compiled a wheels file for you to use.  You can delete it afterwards if you want.

2. Install the rvc-python library:
   ```
   pip install git+https://github.com/JarodMica/rvc-python
   ```
3. Ensure you have pytorch installed with CUDA enabled [Check Torch Install](#check-torch-install)

### Check Torch Install
Sometimes, torch may be re-installed from other dependencies, so we want to be sure we're on the right version.

Check torch version:
```
pip show torch
```

As long as torch `Version: 2.3.1+cu121`, you should be fine.  If not, follow below:

```
pip uninstall torch -y
pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121
```

Torch is a pretty large download, so it may take a bit of time.  Once you have it installed here, it should be fine following the other install.  However, sometimes, newer versions of torch may uninstall the one we just did, so you may need to uninstall and reinstall after each engine to make sure you have the correction version.  After the first install, it will have been cached, so you won't have to wait each time afterwards.

## Usage
To be written


## Acknowledgements
This has been put together using a variety of open-source models and libraries.  Wouldn't have been possible without them.

TTS Engines:
- Tortoise TTS: https://github.com/neonbjb/tortoise-tts
- StyleTTS: https://github.com/yl4579/StyleTTS2

S2S Engines:
- RVC: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI
  - Installable RVC Library: https://github.com/daswer123/rvc-python
