# Changelog & thoughts

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
