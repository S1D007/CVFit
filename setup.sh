#!/bin/bash
# CVFit Setup Script for macOS/Linux

echo "========================================================="
echo "          Setting up CVFit - Fitness Tracker             "
echo "========================================================="

python_version=$(python3 --version 2>&1)
if [[ $? -ne 0 || ! "$python_version" =~ "Python 3." ]]; then
    echo "❌ Python 3.8 or higher is required."
    echo "Please install Python from https://www.python.org/downloads/"
    exit 1
fi

major_version=$(echo $python_version | cut -d' ' -f2 | cut -d'.' -f1)
minor_version=$(echo $python_version | cut -d' ' -f2 | cut -d'.' -f2)

if (( $major_version < 3 || ($major_version == 3 && $minor_version < 8) )); then
    echo "❌ Python 3.8 or higher is required. You have $python_version."
    echo "Please install a newer version from https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Found $python_version"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir" || exit 1

if [ ! -d "env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv env
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment."
        exit 1
    fi
    echo "✅ Virtual environment created successfully"
else
    echo "✅ Virtual environment already exists"
fi

echo "Activating virtual environment..."
source env/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment."
    exit 1
fi

echo "Installing required packages (this may take a few minutes)..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install required packages."
    echo "Check your internet connection and try again."
    exit 1
fi
echo "✅ Packages installed successfully"

if [ ! -f "yolov8n-pose.pt" ]; then
    echo "Downloading pose detection model..."
    python -c "from ultralytics import YOLO; YOLO('yolov8n-pose.pt')" || {
        echo "❌ Failed to download pose model."
        exit 1
    }
    echo "✅ Pose model downloaded successfully"
else
    echo "✅ Pose model already exists"
fi

echo "========================================================="
echo "🎉 Setup completed successfully! Launching CVFit..."
echo "========================================================="

python cvfit.py

deactivate