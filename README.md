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
- [Text-to-Speech Engines](#text-to-speech-engines)
- [Speech to Speech Engines](#speech-to-speech-engines)
- [Usage](#usage)
- [Acknowledgements](#acknowledgements)

### Install Specific Engines
- [TortoiseTTS Installation](#tortoisetts-installation)
- [StyleTTS 2 Installation](#styletts-2-installation)
- [F5-TTS Installation](#f5-tts-installation)
- [RVC Installation](#rvc-installation)

## Features
:heavy_check_mark: Multi-speaker/engine generation, allowing you to select who speaks which sentence etc.

:heavy_check_mark: Audio playback of individually generated sentences, or playback all to listen as it generates

:heavy_check_mark: Save in place to continue generating later (continue from where you stopped at)

:heavy_check_mark: Bulk sentence regeneration and editting to regenerate audio for a sentence or change which speaker and/or engine is being used for a sentence

:heavy_check_mark: Reloading previous audiobooks and exporting audiobooks

:heavy_check_mark: Sentence remapping in case you need to update the original text file that was used for generation

:heavy_check_mark: Integration with popular open-source models like TortoiseTTS, RVC, StyleTTS, F5TTS, XTTS (to be added) and GPT-SoVITS

## Windows Package Installation
Available for Youtube Channel Members at the Supporter (Package) level: https://www.youtube.com/channel/UCwNdsF7ZXOlrTKhSoGJPnlQ/join or via purchase here: https://buymeacoffee.com/jarodsjourney/extras
### Pre-requisites
- NVIDIA GPU with at least 8GB of VRAM (for heavier inference models like Tortoise, 4-6 GB might be possible as we're not training here)
- Please install the CUDA DEV toolkit here, else `CUDA_HOME` error will occur for RVC: https://developer.nvidia.com/cuda-12-1-0-download-archive?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local

1. Download the zip file provided to you on the members community tab.
2. Unzip the folder
3. To get StyleTTS, double-click and run `finish_styletts_install.bat`
4. Run the `start.bat` file

And that's it! (maybe)

For **F5 TTS**, an additional download will be incurred when you first use it due to licensing of the pretrained base model being cc-by-nc-4.0

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
   git submodule update
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

## Text-to-Speech Engines
### TortoiseTTS Installation
0. Make sure your venv is still activated, if not, activate it, then [pull the repo to update if you are updating an older install](#updating-the-package):
   ```
   .\venv\Scripts\activate
   ```
1. Change directory to tortoise submodule, then pull its submodules:
   ```
   cd .\modules\tortoise_tts_api\
   git submodule init
   git submodule update
   ```
2. Install the submodules:
   ```
   pip install modules\tortoise_tts
   pip install modules\dlas
   ```
3. Install the tortoise tts api repo, then cd back to root:
   ```
   pip install .
   cd ..\..
   ```
4. Ensure you have pytorch installed with CUDA enabled [Check Torch Install](#check-torch-install)

### StyleTTS 2 Installation
0. Make sure your venv is still activated, if not, activate it, then [pull the repo to update if you are updating an older install](#updating-the-package):
   ```
   .\venv\Scripts\activate
   ```
1. Change directory to styletts submodule, then pull its submodules:
   ```
   cd .\modules\styletts-api\
   git submodule init
   git submodule update
   ```
2. Install the submodules:
   ```
   pip install modules\StyleTTS2
   ```
3. Install the styletts api repo, then cd back to root:
   ```
   pip install .
   cd ..\..
   ```
4. Install monotonic align with the precompiled wheels that I've built [here](https://huggingface.co/Jmica/audiobook_models/blob/main/monotonic_align-1.2-cp311-cp311-win_amd64.whl), put in the repo root, and run the below command.  Will NOT work if you wanna use a different version of python:
   ```
   pip install monotonic_align-1.2-cp311-cp311-win_amd64.whl
   ```
   - Alternatively, if you are running a different python version, you will need microsoft c++ build tools to install it yourself: https://visualstudio.microsoft.com/downloads/?q=build+tools
      ```
      pip install git+https://github.com/resemble-ai/monotonic_align.git@78b985be210a03d08bc3acc01c4df0442105366f
      ```
   
5. Get eSpeak-NG files and base STTS2 model by running the `finish_styletts_install.bat`:
   ```
   .\finish_styletts_install.bat
   ```
   - Alternatively, install eSpeak-NG onto your computer. Head over to https://github.com/espeak-ng/espeak-ng/releases and select the espeak-ng-X64.msi the assets dropdown. Download, run, and follow the prompts to set it up on your device. As of this write-up, it'll be at the bottom of 1.51 on the github releases page
      - You will also need to add the following to your envrionment path:
      ```
      PHONEMIZER_ESPEAK_LIBRARY="c:\Program Files\eSpeak NG\libespeak-ng.dll"
      PHONEMIZER_ESPEAK_PATH =“c:\Program Files\eSpeak NG”
      ```

6. Ensure you have pytorch installed with CUDA enabled [Check Torch Install](#check-torch-install)

### F5-TTS Installation
0. Make sure your venv is still activated, if not, activate it, then [pull the repo to update if you are updating an older install](#updating-the-package):
   ```
   .\venv\Scripts\activate
   ```
1. Install the F5-TTS submodule as a package:
   ```
   pip install .\modules\F5-TTS
   ```
2. Ensure you have pytorch installed with CUDA enabled [Check Torch Install](#check-torch-install)

### GPT-SoVITS Installation
0. Make sure your venv is still activated, if not, activate it, then [pull the repo to update if you are updating an older install](#updating-the-package):
   ```
   .\venv\Scripts\activate
   ```
1. Install the GPT-SoVITS-Package submodule:
   ```
   pip install .\modules\GPT-SoVITS-Package\
   ```
2. Inside of , GPT-SoVITS base models will automatically be downloaded when first starting a generation.  Anytime there is a new update to the remote HF repo, it will download new files.  This behavior can be disabled by turning `auto_download_gpt_sovits` inside of `config\setting.yaml` to `False` instead of `True`.
3. Ensure you have pytorch installed with CUDA enabled [Check Torch Install](#check-torch-install)

## Speech-to-Speech Engines
### RVC Installation
0. Make sure your venv is still activated, if not, activate it, then [pull the repo to update if you are updating an older install](#updating-the-package):
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
   pip install .\modules\rvc-python\
   ```
3. Ensure you have pytorch installed with CUDA enabled [Check Torch Install](#check-torch-install)

### Check Torch Install
Sometimes, torch may be re-installed from other dependencies, so we want to be sure we're on the right version.

Check torch version:
```
pip show torch
```

As long as torch `Version: 2.7.0+cu126`, you should be fine.  If not, follow below:
> Blackwell GPUs (NVIDIA 50 series) need pytorch 2.7.0 or higher
```
pip uninstall torch -y
pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu126
```

Torch is a pretty large download, so it may take a bit of time.  Once you have it installed here, it should be fine following the other install.  However, sometimes, newer versions of torch may uninstall the one we just did, so you may need to uninstall and reinstall after each engine to make sure you have the correction version.  After the first install, it will have been cached, so you won't have to wait each time afterwards.

### Updating the Package
If there are updates to the Audiobook Maker, you may need to `pull` new files from the source repo in order to gain access to new functionality. 
1. Open up a terminal in the Audiobook Maker folder (if not openned alread) and run:
   ```
   git pull
   git submodule update
   ```
If you run into issues where you can't pull the updates, you may have made edits to the code base.  In this case, you will need to `stash` your updates so that you can `pull` it.  I won't go over how you can reapply custom mods as that dives into git conflicts etc.
   ```
   git stash
   git pull
   git submodule update
   ```

## Usage
To be written


## Acknowledgements
This has been put together using a variety of open-source models and libraries.  Wouldn't have been possible without them.

TTS Engines:
- Tortoise TTS: https://github.com/neonbjb/tortoise-tts
- StyleTTS: https://github.com/yl4579/StyleTTS2
- F5TTS: https://github.com/SWivid/F5-TTS/tree/main
- GPT-SoVITS: https://github.com/RVC-Boss/GPT-SoVITS

S2S Engines:
- RVC: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI
  - Installable RVC Library: https://github.com/daswer123/rvc-python

## Licensing
Each engine being used here is MIT or Apache-2.0.  However, base-pretrained models may have their own licenses or use limitations so please be aware of that depending on your use case. I am not a lawyer, so I will just state what the licenses are.

### StyleTTS 2
The pretrained model states: 
>*Before using these pre-trained models, you agree to inform the listeners that the speech samples are synthesized by the pre-trained models, unless you have the permission to use the voice you synthesize. That is, you agree to only use voices whose speakers grant the permission to have their voice cloned, either directly or by license before making synthesized voices public, or you have to publicly announce that these voices are synthesized if you do not have the permission to use these voices.*

### F5 TTS
The pretrained base was trained on the [Emilia dataset](https://huggingface.co/datasets/amphion/Emilia-Dataset), so it is Non-Commerical CC-By-NC-4.0.

