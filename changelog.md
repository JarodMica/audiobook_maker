# Changelog & thoughts

# 6/9/2024
Bug fix for tortoise TTS API call implemented, lots of things in the pipeline need a little refreshing
- Package version is not done yet.

# 10/17/2023
Bug fixes for next patch
- Fixed hardcoded path in lightweight rvc package under configs.py for nvidia cards under 4GB

# 10/16/2023
Needed a more robust way to parse sentences in the audiobook maker, as it was messing up on sentences: https://github.com/JarodMica/audiobook_maker/issues/15.  Instead of manually defining splits, found that there is a python library and model that can help called nltk https://github.com/nltk/nltk.  Incoporated this into the tortoise_api.py and should add to the robustness of the code to handle more text.

# 10/8/2023
Had some people try out the package and found an issue that was caused due to python for some reason still accessing the user's local installation of python.  This was leading to conflicting package issues between global and runtime packages.
- Added logic that checks if a runtime folder is located in the parent directory of the audiobook maker
    - If runtime is found, removes global and user from sys.path and then adds the runtime package to sys.path
        - This resolved the issue the user was experiencing so that the embedded python package is run in isolation
- Added feature to save the settings used in the previous generation of an audiobook, the value is saved in generation_setting.json
- Added ability to add a background image to the GUI just because I want one
- Adjusted filter paragraphs in tortoise to handle the sentence list better, removing non-alphabetic sentences

# 10/7/2023
Preparing for a distributable Nvidia-Windows release
- Added a small addition to include directory of running script for sys.path so that the package version can see the tortoise module
- Added some batch files for quicker python installation
    - setup_cuda.bat still requires you download rvc manually
- Updated the way ```rvc_infer``` is called due to updates in rvc-tts-pipe @ lightweight, now it requires accessing the module ```rvc_pipe``` for the full import of ```from rvc_pipe.rvc_infer import rvc_convert```

## Notes for myself:
- Worked on getting things all "packaged" up, venv files are not distributable as previously known, so the way around this is by creating a portable python instllation via the embeddable packages, for example at the bottom: https://www.python.org/downloads/release/python-31011/
    - Once downloaded and extracted, you have to set up everything inside of any folder (aka: runtime), so all installations will be here.
    - The first thing you need is to get pip installed which can be found here: https://github.com/pypa/get-pip and go get it on the bootstrap page
        - Can then install with something like .\python.exe get-pip.py
    - After you have pip installed, you can then install everything into the runtime, by using pip as a module
    - One important note is that you need to also uncomment import site inside of the python310._pth file in order for site-packages to work correctly
    

# 10/1/2023
LOTS of refactoring in the code, just about every method has been updated to accomodate the new data structure and renewed logic in how everything interacts.  I can't outline everything, but basically, a majority of the changes revolve around correctly grabbing the mapping of audio to sentence so that it plays, regenerates, loads, updates, and continues much more dynamically than before, with everything contained in the text_audio_map.json
- Add a "generated" key inside of the idx value dictionary to determine whether or not a sentence has been generated already
- Added an "update" button that allows you to use either modifed or new sentences with an audiobook without having to regenerate the whole thing
    - It will delete old audio files of sentences that are no longer detected, reorder the sentences in text_audio_map.json so that it plays in the correct order, and will generate new audio for them if chosen.
- Added "continue" button that will continue from where the last generation left off
- Added a "Pause Between Sentences" slider for export
    - Personally, will probably be better if silence can be added after sentences invidually as well, this could be an option too.
- Will probably be easier to make a new tab that deals with export of the audiobooks
- Got rid of v1 of the audiobook maker
    

# 9/28/2023
A work in progress, currently adding the ability to "update" an audio book so that you can change the text file, modify a sentence, etc. without having to regenerate everything
- Now the proof of concept is done, working on a more complex data structure to make the application more robust to additional features.
    - Introduced a text_audio_map.json that uses index number as a key, and then stores its value in a dictionary which contains the sentence and then audio path(relative to the app)

Need to continue working on: 
- Fixing the other buttons so that it works with the new data structure
- Testing for bugs 

# 9/19/2023
Changing quite a bit of things as I thought through a refactor.  Going to make this one single python script which is going to be ```audio_book_app_2_0.py```
- Created an entirely new script to handle audio book making, integrated with both Tortoise and RVC
- Cleaned out and removed the narrtion python scripts
- Renamed old audio_book_maker to audio_book_app_1_0.py
    - I will eventually remove it, but its there for history sake in case I need to reference anything from it


# 8/22/2023
So I added in RVC to the audiobook maker, narration_audiobook_individual_files.py will NOT work ATM unless RVC is installed, need to adjust this later so that you can choose which tts to use
- Added in RVC to the audiobook generator

Plans and notes moving forward
- Work on easy parameter changing
- Allow for other TTS engines
- Give an RVC off/on button
- Convert everything into a gradio interface
