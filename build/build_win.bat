@echo off
echo Building Volt-AI for Windows...
pyinstaller zyvo.spec
if exist dist\Volt-AI.exe (
    echo.
    echo Build successful!
    echo Executable: dist\Volt-AI.exe
) else (
    echo.
    echo Build failed!
    exit /b 1
)