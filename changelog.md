# Changelog & thoughts

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
