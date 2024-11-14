@echo off
if exist "runtime\" (
    runtime\python.exe -m pip install nltk
    runtime\python.exe .\modules\styletts-api\modules\StyleTTS2\styletts2\download_punkt.py
    portable_git\bin\git.exe clone https://github.com/JarodMica/eSpeak-Files.git
    xcopy "eSpeak-Files\eSpeak NG" "eSpeak NG" /E /I /H /Y
    rmdir /S /Q "eSpeak-Files"
) else (
    call venv\Scripts\activate
    pip install nltk
    python .\modules\styletts-api\modules\StyleTTS2\styletts2\download_punkt.py
    git clone https://github.com/JarodMica/eSpeak-Files.git
    xcopy "eSpeak-Files\eSpeak NG" "eSpeak NG" /E /I /H /Y
    rmdir /S /Q "eSpeak-Files"
)

@echo eSpeak NG should be in the root directory now, please check!