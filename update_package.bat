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
xcopy %REPO_NAME%\up.bat up.bat /E /I /H /Y

call up.bat