#!/bin/bash
set -e
echo "Building Volt-AI for Linux..."
pyinstaller zyvo.spec
if [ -f dist/Volt-AI ]; then
    echo ""
    echo "Build successful!"
    echo "Executable: dist/Volt-AI"
else
    echo ""
    echo "Build failed!"
    exit 1
fi