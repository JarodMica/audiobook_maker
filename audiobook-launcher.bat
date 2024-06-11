@echo off
REM Audiobook Maker Launcher
REM Created by: Deffcolony
REM Github: https://github.com/JarodMica/audiobook_maker
REM
REM Description:
REM This script can install Audiobook Maker
REM
REM This script is intended for use on Windows systems.
REM report any issues or bugs on the GitHub repository.
REM
REM GitHub: https://github.com/deffcolony/ai-toolbox
REM Issues: https://github.com/deffcolony/ai-toolbox/issues
title Audiobook Maker Launcher
setlocal

REM ANSI Escape Code for Colors
set "reset=[0m"

REM Strong Foreground Colors
set "white_fg_strong=[90m"
set "red_fg_strong=[91m"
set "green_fg_strong=[92m"
set "yellow_fg_strong=[93m"
set "blue_fg_strong=[94m"
set "magenta_fg_strong=[95m"
set "cyan_fg_strong=[96m"

REM Normal Background Colors
set "red_bg=[41m"
set "blue_bg=[44m"

REM Environment Variables (winget)
set "winget_path=%userprofile%\AppData\Local\Microsoft\WindowsApps"

REM Environment Variables (TOOLBOX Install Extras)
set "miniconda_path=%userprofile%\miniconda"

REM Environment Variables (TOOLBOX FFmpeg)
set "ffmpeg_url=https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z"
set "ffdownload_path=%~dp0ffmpeg.7z"
set "ffextract_path=C:\ffmpeg"
set "bin_path=%ffextract_path%\bin"

REM Define the paths and filenames for the shortcut creation
set "shortcutTarget=%~dp0audiobook-launcher.bat"
set "iconFile=%~dp0audiobook-maker.ico"
set "desktopPath=%userprofile%\Desktop"
set "shortcutName=audiobook-launcher.lnk"
set "startIn=%~dp0"
set "comment=Audiobook Maker Launcher"


REM Check if Winget is installed; if not, then install it
winget --version > nul 2>&1
if %errorlevel% neq 0 (
    echo %yellow_bg%[%time%]%reset% %yellow_fg_strong%[WARN] Winget is not installed on this system.%reset%
    echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Installing Winget...
    bitsadmin /transfer "Microsoft.DesktopAppInstaller_8wekyb3d8bbwe" /download /priority FOREGROUND "https://github.com/microsoft/winget-cli/releases/download/v1.5.2201/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle" "%temp%\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
    start "" "%temp%\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
    echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% %green_fg_strong%Winget installed successfully.%reset%
) else (
    echo %blue_fg_strong%[INFO] Winget is already installed.%reset%
)

rem Get the current PATH value from the registry
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH') do set "current_path=%%B"

rem Check if the paths are already in the current PATH
echo %current_path% | find /i "%winget_path%" > nul
set "ff_path_exists=%errorlevel%"

rem Append the new paths to the current PATH only if they don't exist
if %ff_path_exists% neq 0 (
    set "new_path=%current_path%;%winget_path%"

    rem Update the PATH value in the registry
    reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%new_path%" /f

    rem Update the PATH value for the current session
    setx PATH "%new_path%" > nul
    echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% %green_fg_strong%winget successfully added to PATH.%reset%
) else (
    set "new_path=%current_path%"
    echo %blue_fg_strong%[INFO] winget already exists in PATH.%reset%
)

REM Check if Git is installed if not then install git
git --version > nul 2>&1
if %errorlevel% neq 0 (
    echo %yellow_bg%[%time%]%reset% %yellow_fg_strong%[WARN] Git is not installed on this system.%reset%
    echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Installing Git using Winget...
    winget install -e --id Git.Git
    echo echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% %green_fg_strong%Git is installed. Please restart the Launcher.%reset%
    pause
    exit
) else (
    echo %blue_fg_strong%[INFO] Git is already installed.%reset%
)


REM home Frontend
:home
title Audiobook Maker [HOME]
cls
echo %blue_fg_strong%/ Home %reset%
echo -------------------------------------
echo What would you like to do?
echo 1. Install Audiobook Maker
echo 2. Run Audiobook Maker
echo 3. Update
echo 4. Uninstall Audiobook Maker
echo 5. Exit


set "choice="
set /p "choice=Choose Your Destiny: "

REM Default to choice 1 if no input is provided
REM Disable REM below to enable default choise
REM if not defined choice set "choice=1"

REM home - Backend
if "%choice%"=="1" (
    call :install_audiobook_maker
) else if "%choice%"=="2" (
    call :run_audiobook_maker
) else if "%choice%"=="3" (
    call :update_audiobook_maker
) else if "%choice%"=="4" (
    call :uninstall_audiobook_maker
) else if "%choice%"=="5" (
    exit
) else (
    color 6
    echo WARNING: Invalid number. Please insert a valid number.
    pause
    goto :home
)


:install_audiobook_maker
title Audiobook Maker [INSTALL]
cls
echo %blue_fg_strong%/ Home / Install Audiobook Maker%reset%
echo ---------------------------------------------------------------
echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Installing Audiobook Maker...
echo %cyan_fg_strong%This may take a while. Please be patient.%reset%

echo %blue_fg_strong%[INFO]%reset% Installing 7-Zip...
winget install -e --id 7zip.7zip

rem Get the current PATH value from the registry
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH') do set "current_path=%%B"

rem Check if the paths are already in the current PATH
echo %current_path% | find /i "%zip7_install_path%" > nul
set "zip7_path_exists=%errorlevel%"

rem Append the new paths to the current PATH only if they don't exist
if %zip7_path_exists% neq 0 (
    set "new_path=%current_path%;%zip7_install_path%"
    echo %green_fg_strong%7-Zip added to PATH.%reset%
) else (
    set "new_path=%current_path%"
    echo %blue_fg_strong%[INFO] 7-Zip already exists in PATH.%reset%
)

rem Update the PATH value in the registry
reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%new_path%" /f

rem Update the PATH value for the current session
setx PATH "%new_path%" > nul

echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% %green_fg_strong%7-Zip installed successfully. Please restart the Launcher.%reset%

rem install FFmpeg
echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Downloading FFmpeg archive...
curl -L -o "%ffdownload_path%" "%ffmpeg_url%"

echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Creating ffmpeg directory if it doesn't exist...
if not exist "%ffextract_path%" (
    mkdir "%ffextract_path%"
)

echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Extracting FFmpeg archive...
7z x "%ffdownload_path%" -o"%ffextract_path%"


echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Moving FFmpeg contents to C:\ffmpeg...
for /d %%i in ("%ffextract_path%\ffmpeg-*-full_build") do (
    xcopy "%%i\bin" "%ffextract_path%\bin" /E /I /Y
    xcopy "%%i\doc" "%ffextract_path%\doc" /E /I /Y
    xcopy "%%i\presets" "%ffextract_path%\presets" /E /I /Y
    rd "%%i" /S /Q
)

rem Get the current PATH value from the registry
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH') do set "current_path=%%B"

rem Check if the paths are already in the current PATH
echo %current_path% | find /i "%bin_path%" > nul
set "ff_path_exists=%errorlevel%"

rem Append the new paths to the current PATH only if they don't exist
if %ff_path_exists% neq 0 (
    set "new_path=%current_path%;%bin_path%"
    echo %green_fg_strong%ffmpeg added to PATH.%reset%
) else (
    set "new_path=%current_path%"
    echo %blue_fg_strong%[INFO] ffmpeg already exists in PATH.%reset%
)

rem Update the PATH value in the registry
reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%new_path%" /f

rem Update the PATH value for the current session
setx PATH "%new_path%" > nul

del "%ffdownload_path%"
echo %green_fg_strong%FFmpeg is installed. Please restart the Launcher.%reset%


REM Clone the Audiobook Maker repository
echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Cloning the Audiobook Maker repository...
git clone https://github.com/JarodMica/audiobook_maker.git

echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Installing Miniconda...
winget install -e --id Anaconda.Miniconda3

REM Run conda activate from the Miniconda installation
echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Activating Miniconda environment...
call "%miniconda_path%\Scripts\activate.bat"

REM Create a Conda environment named audiobook-maker
echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Creating Conda environment audiobook-maker...
call conda create -n audiobook-maker -y

REM Activate the audiobook-maker Maker environment
echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Activating Conda environment audiobook-maker...
call conda activate audiobook-maker

REM Install Python and Git in the audiobook-maker environment
echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Installing Python and Git in the Conda environment...
call conda install python=3.10 -y

REM Download rvc_lightweight 7z archive
curl -L -o "%~dp0rvc_lightweight.7z" "https://huggingface.co/Jmica/rvc/resolve/main/rvc_lightweight.7z" || (
    color 4
    echo %red_bg%[%time%]%reset% %red_fg_strong%[ERROR] Download failed. Please try again.%reset%
    pause
    goto :home
)

REM Extract rvc_lightweight 7z archive
"%ProgramFiles%\7-Zip\7z.exe" x "%~dp0rvc_lightweight.7z" -o"%~dp0rvc_lightweight" || (
    color 4
    echo %red_bg%[%time%]%reset% %red_fg_strong%[ERROR] Extraction failed. Please try again.%reset%
    pause
    goto :home
)

ren "%~dp0rvc_lightweight\rvc_lightweight" "rvc"

REM Copy rvc folder to audiobook_maker
xcopy /E /I /Y "%~dp0rvc_lightweight\rvc" "%~dp0audiobook_maker\rvc"

REM Remove rvc_lightweight leftovers
del "%~dp0rvc_lightweight.7z"
rd /S /Q "%~dp0rvc_lightweight"

cd /d "%~dp0audiobook_maker"
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
pip install -r requirements.txt
pip install -r rvc/requirements.txt
pip install https://huggingface.co/Jmica/rvc/resolve/main/fairseq-0.12.2-cp310-cp310-win_amd64.whl
pip install git+https://github.com/JarodMica/rvc-tts-pipeline.git@lightweight#egg=rvc_tts_pipe


echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% %green_fg_strong%Audiobook Maker successfully installed.%reset%

REM Ask if the user wants to create a shortcut
set /p create_shortcut=Do you want to create a shortcut on the desktop? [Y/n] 
if /i "%create_shortcut%"=="Y" (

    REM Create the shortcut
    echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Creating shortcut...
    %SystemRoot%\system32\WindowsPowerShell\v1.0\powershell.exe -Command ^
        "$WshShell = New-Object -ComObject WScript.Shell; " ^
        "$Shortcut = $WshShell.CreateShortcut('%desktopPath%\%shortcutName%'); " ^
        "$Shortcut.TargetPath = '%shortcutTarget%'; " ^
        "$Shortcut.IconLocation = '%iconFile%'; " ^
        "$Shortcut.WorkingDirectory = '%startIn%'; " ^
        "$Shortcut.Description = '%comment%'; " ^
        "$Shortcut.Save()"
    echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% %green_fg_strong%Shortcut created on the desktop.%reset%
    pause
)
goto :home


:run_audiobook_maker
title Audiobook Maker
cls
echo %blue_fg_strong%/ Home / Run Audiobook Maker%reset%
echo ---------------------------------------------------------------

REM Run conda activate from the Miniconda installation
call "%miniconda_path%\Scripts\activate.bat"

REM Activate the audiobook-maker environment
call conda activate audiobook-maker

REM Start Audiobook Maker
cd /d "%~dp0audiobook_maker"
start cmd /k python audio_book_app_2_0.py
goto :home


:update_audiobook_maker
title Audiobook Maker [UPDATE]
cls
echo %blue_fg_strong%/ Home / Update%reset%
echo ---------------------------------------------------------------
echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Updating Audiobook Maker...
cd /d "%~dp0audiobook_maker"

REM Check if git is installed
git --version > nul 2>&1
if %errorlevel% neq 0 (
    echo %red_bg%[%time%]%reset% %red_fg_strong%[ERROR] git command not found in PATH. Skipping update.%reset%
    echo %red_bg%Please make sure Git is installed and added to your PATH.%reset%
) else (
    call git pull --rebase --autostash
    if %errorlevel% neq 0 (
        REM incase there is still something wrong
        echo %red_bg%[%time%]%reset% %red_fg_strong%[ERROR] Errors while updating. Please download the latest version manually.%reset%
    ) else (
        echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% %green_fg_strong%Audiobook Maker updated successfully.%reset%
    )
)
pause
goto :home

:uninstall_audiobook_maker
title Audiobook Maker [UNINSTALL]
setlocal enabledelayedexpansion
chcp 65001 > nul

REM Confirm with the user before proceeding
echo.
echo %red_bg%╔════ DANGER ZONE ══════════════════════════════════════════════════════════════════════════════╗%reset%
echo %red_bg%║ WARNING: This will delete all data of Audiobook Maker                                         ║%reset%
echo %red_bg%║ If you want to keep any data, make sure to create a backup before proceeding.                 ║%reset%
echo %red_bg%╚═══════════════════════════════════════════════════════════════════════════════════════════════╝%reset%
echo.
set /p "confirmation=Are you sure you want to proceed? [Y/N]: "
if /i "%confirmation%"=="Y" (

    REM Remove the Conda environment
    echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Removing the Conda environment 'audiobook-maker'...
    call conda remove --name audiobook-maker --all -y

    REM Remove the folder audiobook_maker
    echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Removing the audiobook_maker Maker directory...
    cd /d "%~dp0"
    rmdir /s /q audiobook_maker

    echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% %green_fg_strong%Audiobook Maker uninstalled successfully.%reset%
    pause
    goto :home
) else (
    echo %blue_bg%[%time%]%reset% %blue_fg_strong%[INFO]%reset% Uninstall canceled.
    pause
    goto :home
)