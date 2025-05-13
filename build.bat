@echo off
Title Python to EXE Builder

:: Check if Python is installed
python --version 3>NUL
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Check if pip is available
pip --version >NUL 2>&1
if errorlevel 1 (
    echo Error: pip is not installed or not in PATH.
    pause
    exit /b 1
)

:: Install required dependencies (including PyInstaller)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

:: Build the executable using PyInstaller
cls
Title Building EXE...
python -m PyInstaller --onefile --clean --icon=icon.ico --version-file=version.txt src/DiscordSpammer.py

:: Check if build was successful
if errorlevel 1 (
    echo Error: Build failed! Check for errors above.
    pause
    exit /b 1
)

echo Build completed successfully!
echo The EXE is in the 'dist' folder.
pause