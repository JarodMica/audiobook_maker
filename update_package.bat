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

portable_git\bin\git.exe clone https://github.com/JarodMica/%REPO_NAME%.git
cd %REPO_NAME%
git submodule init
git submodule update --remote
cd ..

xcopy %REPO_NAME%\update_package.bat update_package.bat /E /I /H /Y
xcopy %REPO_NAME%\requirements.txt requirements.txt /E /I /H /Y

xcopy %REPO_NAME%\src src /E /I /H
xcopy %REPO_NAME%\configs configs /E /I /H
xcopy %REPO_NAME%\modules\tortoise_tts_api modules\tortoise_tts_api /E /I /H /Y
cd modules\tortoise_tts_api
git submodule init
git submodule update --remote
cd ..\..

runtime\python.exe -m pip uninstall tortoise_tts_api
runtime\python.exe -m pip uninstall dlas
runtime\python.exe -m pip uninstall tortoise
runtime\python.exe -m pip install modules\tortoise_tts_api\modules\tortoise_tts
runtime\python.exe -m pip install modules\tortoise_tts_api\modules\dlas
runtime\python.exe -m pip install modules\tortoise_tts_api

runtime\python.exe -m pip uninstall rvc-python
runtime\python.exe -m pip install git+https://github.com/JarodMica/rvc-python

runtime\python.exe -m pip install -r requirements.txt

@echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@echo Finished updating!
@echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@echo ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pause