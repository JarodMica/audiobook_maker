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

cd engines\styletts
mkdir base
cd base

set download_stts_base=https://huggingface.co/yl4579/StyleTTS2-LibriTTS/resolve/d2ca3f14cf019cd2da653c74564e04f8e1f5c5ab/Models/LibriTTS/epochs_2nd_00020.pth?download=true
set file_name_stts_base=epochs_2nd_00020.pth
if not exist "%file_name_stts_base%" (
    echo Downloading %file_name_stts_base%...
    curl -L -O "%download_stts_base%"
    if errorlevel 1 (
        echo Download failed. Please check your internet connection or the URL and try again.
        exit /b 1
    )
) else (
    echo File %file_name_stts_base% already exists, skipping download.
)

set download_stts_conf=https://huggingface.co/yl4579/StyleTTS2-LibriTTS/resolve/d2ca3f14cf019cd2da653c74564e04f8e1f5c5ab/Models/LibriTTS/config.yml?download=true
set file_name_stts_conf=config.yml
if not exist "%file_name_stts_conf%" (
    echo Downloading %file_name_stts_conf%...
    curl -L -O "%download_stts_conf%"
    if errorlevel 1 (
        echo Download failed. Please check your internet connection or the URL and try again.
        exit /b 1
    )
) else (
    echo File %file_name_stts_conf% already exists, skipping download.
)

@echo eSpeak NG should be in the root directory now, please check!
pause