@echo off

set REPO_NAME=audiobook_maker

if not exist "runtime" (
    @echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    echo This is not the packaged version, if you are trying to update your manual installation, please use git pull instead
    @echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    pause
    exit /b
)

if exist "%REPO_NAME%" (
    @echo It looks like you've already cloned the repository for updating before.
    @echo If you want to continue with updating, type y.
    @echo Else, type n.
    choice /M "Do you want to continue?"
    if errorlevel 2 (
        @echo Exiting the script...
        exit /b
    )
    rmdir /S /Q "%REPO_NAME%"
)

set PATH=%~dp0portable_git\bin;%PATH%

git clone https://github.com/JarodMica/%REPO_NAME%.git
cd %REPO_NAME%
git submodule init
git submodule update --remote

REM Store the cloned head commit hash
for /f %%i in ('git rev-parse HEAD') do set cloned_head=%%i
cd ..

REM Store the current head commit hash
for /f %%i in ('git rev-parse HEAD') do set current_head=%%i

@echo Latest Version = %cloned_head%
@echo Current Version = %current_head%

if "%cloned_head%"=="%current_head%" (
    @echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @echo The versions are the same; there is no new update.
    @echo Only proceed if you understand what you're doing. If not, type N to exit the script and stop updating.
    choice /M "Do you want to continue?"
    if errorlevel 2 (
        @echo Exiting the script...
        exit /b
    )
)

xcopy %REPO_NAME%\update_package.bat update_package.bat /E /I /H /Y
xcopy %REPO_NAME%\requirements.txt requirements.txt /E /I /H /Y
xcopy %REPO_NAME%\.git .git /E /I /H /Y

xcopy %REPO_NAME%\src src /E /I /H /Y
xcopy %REPO_NAME%\configs configs /E /I /H /Y
xcopy %REPO_NAME%\modules\tortoise_tts_api modules\tortoise_tts_api /E /I /H /Y
xcopy %REPO_NAME%\modules\styletts-api modules\styletts-api /E /I /H /Y

cd modules\tortoise_tts_api
git submodule init
git submodule update --remote
cd ..\..

runtime\python.exe -m pip uninstall -y tortoise_tts_api
runtime\python.exe -m pip uninstall -y dlas
runtime\python.exe -m pip uninstall -y tortoise
runtime\python.exe -m pip install modules\tortoise_tts_api\modules\tortoise_tts
runtime\python.exe -m pip install modules\tortoise_tts_api\modules\dlas
runtime\python.exe -m pip install modules\tortoise_tts_api

set download_monotonic_align=https://huggingface.co/Jmica/audiobook_models/resolve/main/monotonic_align-1.2-cp311-cp311-win_amd64.whl?download=true
set file_name_ma=monotonic_align-1.2-cp311-cp311-win_amd64.wh
if not exist "%file_name_ma%" (
    echo Downloading %file_name_ma%...
    curl -L -O "%download_monotonic_align%"
    if errorlevel 1 (
        echo Download failed. Please check your internet connection or the URL and try again.
        exit /b 1
    )
) else (
    echo File %file_name_ma% already exists, skipping download.
)

runtime\python.exe -m pip install monotonic_align-1.2-cp311-cp311-win_amd64.whl

cd modules\styletts-api
git submodule init
git submodule update --remote
cd ..\..
runtime\python.exe -m pip uninstall -y styletts2
runtime\python.exe -m pip uninstall -y styletts-api
runtime\python.exe -m pip install modules\styletts-api\modules\StyleTTS2
runtime\python.exe -m pip install modules\styletts-api

runtime\python.exe -m pip uninstall -y rvc-python
runtime\python.exe -m pip install git+https://github.com/JarodMica/rvc-python

runtime\python.exe -m pip install -r requirements.txt

@echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@echo Finished updating!
@echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pause