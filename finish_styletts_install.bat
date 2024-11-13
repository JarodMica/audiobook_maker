
if exist "runtime" (
    set PATH=%~dp0portable_git\bin;%PATH%
    runtime\python.exe -m pip install nltk
    runtime\python.exe .\modules\styletts-api\modules\StyleTTS2\styletts2\download_punkt.py
)

git clone https://github.com/JarodMica/eSpeak-Files.git
xcopy "eSpeak-Files\eSpeak NG" "eSpeak NG" /E /I /H /Y
rmdir /S /Q "eSpeak-Files"

@echo eSpeak NG should be in the root directory now, please check!