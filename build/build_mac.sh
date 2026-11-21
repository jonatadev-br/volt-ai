#!/bin/bash
set -e
echo "Building Volt-AI for macOS..."
pyinstaller zyvo.spec
if [ -f dist/Volt-AI ]; then
    echo ""
    echo "Build successful!"
    echo "Executable: dist/Volt-AI"
    echo ""
    echo "To create .app bundle (optional):"
    echo "  py2applet --make-setup main.py"
    echo "  python setup.py py2app"
else
    echo ""
    echo "Build failed!"
    exit 1
fi