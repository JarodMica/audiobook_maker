# Changelog & thoughts

## v3.6.4
- Convert uploaded audio files to .wav for compatibilty
- Add versioning, the app now has a version number with the title
- Move global settings to be loaded in controller.py and passed to model and view instead of loaded in model.

## v3.6.3
- add x_transformers to requirements.txt as needed by GPT-SoVITS
- Added to instructions where GPT-SoVITS requires additional nltk downloads
    ```
    import nltk
    nltk.download('averaged_perceptron_tagger_eng')
    ```
- Put fairseq import into rvc exception block
- Fix autodownload for gpt_sovits models

## v3.6.2
- Fixed parsing bugs that didn't allow for .ckpt and .pt sovits models to be seen in file explorer
- Fixed GPT-SoVITs package for inference with custom models
    - Allow for v4 vocoder to be used wih v3 GPT models (Still, I highly recommend you use the same version of model)

## v3.6.1
### Logic and Engines
- Fix rvc-python package for inference
    - Mainly hubert section causing issues - requires `torch.serialization.add_safe_globals([fairseq.data.dictionary.Dictionary])` inside of `s2s_engines.py` for newer pytorch due to weight_only force.
    - `corpus_key` parameter added to `get_hubert.py` extract features to resolve `get_hubert_model.<locals>._extract_features() got an unexpected keyword argument 'corpus_key'`
- Fix a monkey-patch in GPT-SoVITS which was conflicting with fairseq's usage of `multi_head_attention_forward`, it now uses the patched up version directly `from GPT_SoVITS.AR.modules.patched_mha_with_cache import multi_head_attention_forward_patched`
- Reapply tortoise patch to look for voices correctly
### Gui Enhancements
- Font size is now saved between uses
- Loading background image is now fixed

## v3.6
- Add GPT_SoVITS as a useable engine
- Modify word replacer with updates from PhyEngineer (Ed)
- Update compatibilty of Engines to work with Pytorch>=2.7.0
    - This enables Blackwell (50 series) NVIDIA GPUs
- Tidy up voices folder to separate voices between engines
- Add an uploads menu button for models and voices instead of users having to manually create them
- Text file loading no longer splits based on internal logic and critiera, simply splits sentences based on which sentences are on a newline (allows for more flexibilty in loading, but may cause issues with longer sentences)
- Sentence deletion logic now adjusts the name of the audio file as well so that it matches with the text_audio_map index


## v3.5
- Fix a particularly nasty inefficiency which was causing extremly long loading times for long text files
    - Long text files (greater than 10k lines) will still have significant loading time, depending on your CPU.  28k lines on my PC took around 2 minutes of loading time with a 13900k.
    - It comes from calculating the height of each row for sentences based on # of word wraps
- Added new "Find and replace" feature, a contribution from PhyEngineer.  Thanks Ed! This can be found under the "Tools" menu bar option
    - Menu Bar:
        - File:
            - New List - Create a new list of replacements
            - Load List - Load an existing list of replacements
            - Save - Save current list.  The list must be located in the directory of the audiobook maker
            - Save as - Save current list to a user specified location
    - Add Word - Add a replacement to the table
    - Sort List - Sort replacement list in table alphabetically
    - Delete Word - Delete chosen row in replacements table
    - Speakers Available - Speakers set-up in the audiobook maker to use
    - Test Word - Test a word with the chosen speaker, you can test out the original word or the new word by clicking on the pertinent cell
    - Do Extras - Cleans unwanted characters, replaces common abbreviations with full words (e.g., "Mr." to "Mister"), adjusts punctuation for better audio processing, and eliminates excess whitespace
    - Start Word Replacement - Replace all instances of a word in the currently loaded audiobook

## v3.4
- Remove regen mode (Unintuitive and glad to be rid of it)
- Bulk regeneration replaces regen mode and is now handled with a "Regenerate in Bulk" button and a "Regen" column where users can individually toggle which sentences they want to toggle
    - The column setting is stored, so if you exit out or crash, when loading the audiobook the checkboxes will repopulate with what to regenerate
    - Regen column can be reset with a button that clears all checkboxes
- Added Speaker and Regen columns to table widget
    - Sentence highlight only on Sentence column
    - Speaker column displays which speaker is being used for the sentence
- Allow for editting sentences inside of the GUI
    - After editting a sentence, it will need to be re-generated which can be done with "Continue Audiobook Generation" as they will be marked "False" as generated
- Allow for deleting sentences inside of the GUI
    - Toggleable with toggle option under "Tools"

**Misc**
- New enhancements md file to look at some of the things I might be working on.
- Default narrator color to black from gray
- Adjustments to GUI elements and positioning
- Added a hide/show engines option
- Changed the way book_text.txt is created to reflect what is actually stored in the audio_text_map and not based on the original text file. The original text is now stored in "original_text_file.txt"
- Force user to input book name before loading text file, fixes possible issues where a book is being set up in a "temp" folder but if user exits out, they won't be able to use these temp settings. Fixes some other bugs too.

## 9/18/2024
Got tortoise TTS implemnted, next is styletts2

# Version 3 IN PROGRESS

## 6/9/2024
Bug fix for tortoise TTS API call implemented, lots of things in the pipeline need a little refreshing
- Package version is not done yet.

## 10/17/2023
Bug fixes for next patch
- Fixed hardcoded path in lightweight rvc package under configs.py for nvidia cards under 4GB

## 10/16/2023
Needed a more robust way to parse sentences in the audiobook maker, as it was messing up on sentences: https://github.com/JarodMica/audiobook_maker/issues/15.  Instead of manually defining splits, found that there is a python library and model that can help called nltk https://github.com/nltk/nltk.  Incoporated this into the tortoise_api.py and should add to the robustness of the code to handle more text.

## 10/8/2023
Had some people try out the package and found an issue that was caused due to python for some reason still accessing the user's local installation of python.  This was leading to conflicting package issues between global and runtime packages.
- Added logic that checks if a runtime folder is located in the parent directory of the audiobook maker
    - If runtime is found, removes global and user from sys.path and then adds the runtime package to sys.path
        - This resolved the issue the user was experiencing so that the embedded python package is run in isolation
- Added feature to save the settings used in the previous generation of an audiobook, the value is saved in generation_setting.json
- Added ability to add a background image to the GUI just because I want one
- Adjusted filter paragraphs in tortoise to handle the sentence list better, removing non-alphabetic sentences

## 10/7/2023
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
    

## 10/1/2023
LOTS of refactoring in the code, just about every method has been updated to accomodate the new data structure and renewed logic in how everything interacts.  I can't outline everything, but basically, a majority of the changes revolve around correctly grabbing the mapping of audio to sentence so that it plays, regenerates, loads, updates, and continues much more dynamically than before, with everything contained in the text_audio_map.json
- Add a "generated" key inside of the idx value dictionary to determine whether or not a sentence has been generated already
- Added an "update" button that allows you to use either modifed or new sentences with an audiobook without having to regenerate the whole thing
    - It will delete old audio files of sentences that are no longer detected, reorder the sentences in text_audio_map.json so that it plays in the correct order, and will generate new audio for them if chosen.
- Added "continue" button that will continue from where the last generation left off
- Added a "Pause Between Sentences" slider for export
    - Personally, will probably be better if silence can be added after sentences invidually as well, this could be an option too.
- Will probably be easier to make a new tab that deals with export of the audiobooks
- Got rid of v1 of the audiobook maker
    

## 9/28/2023
A work in progress, currently adding the ability to "update" an audio book so that you can change the text file, modify a sentence, etc. without having to regenerate everything
- Now the proof of concept is done, working on a more complex data structure to make the application more robust to additional features.
    - Introduced a text_audio_map.json that uses index number as a key, and then stores its value in a dictionary which contains the sentence and then audio path(relative to the app)

Need to continue working on: 
- Fixing the other buttons so that it works with the new data structure
- Testing for bugs 

## 9/19/2023
Changing quite a bit of things as I thought through a refactor.  Going to make this one single python script which is going to be ```audio_book_app_2_0.py```
- Created an entirely new script to handle audio book making, integrated with both Tortoise and RVC
- Cleaned out and removed the narrtion python scripts
- Renamed old audio_book_maker to audio_book_app_1_0.py
    - I will eventually remove it, but its there for history sake in case I need to reference anything from it


## 8/22/2023
So I added in RVC to the audiobook maker, narration_audiobook_individual_files.py will NOT work ATM unless RVC is installed, need to adjust this later so that you can choose which tts to use
- Added in RVC to the audiobook generator

Plans and notes moving forward
- Work on easy parameter changing
- Allow for other TTS engines
- Give an RVC off/on button
- Convert everything into a gradio interface
