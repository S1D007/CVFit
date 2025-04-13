# CVFit Setup Script for Windows
# This script sets up all required dependencies and launches CVFit

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Title($message) {
    Write-Output "==========================================================="
    Write-ColorOutput Green "          $message"
    Write-Output "==========================================================="
}

Write-Title "Setting up CVFit - Fitness Tracker"

try {
    $pythonVersion = (python --version 2>&1)
    if (!($pythonVersion -match "Python 3\.(\d+)")) {
        Write-ColorOutput Red "❌ Python 3.8 or higher is required."
        Write-Output "Please install Python from https://www.python.org/downloads/"
        exit 1
    }
    
    $minorVersion = [int]$Matches[1]
    if ($minorVersion -lt 8) {
        Write-ColorOutput Red "❌ Python 3.8 or higher is required. You have $pythonVersion"
        Write-Output "Please install a newer version from https://www.python.org/downloads/"
        exit 1
    }
    
    Write-ColorOutput Green "✅ Found $pythonVersion"
}
catch {
    Write-ColorOutput Red "❌ Python not found or error checking version."
    Write-Output "Please install Python 3.8+ from https://www.python.org/downloads/"
    Write-Output "Make sure to check 'Add Python to PATH' during installation."
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $scriptDir

if (!(Test-Path -Path "env")) {
    Write-Output "Creating virtual environment..."
    try {
        python -m venv env
        if (!$?) {
            Write-ColorOutput Red "❌ Failed to create virtual environment."
            exit 1
        }
        Write-ColorOutput Green "✅ Virtual environment created successfully"
    }
    catch {
        Write-ColorOutput Red "❌ Error creating virtual environment: $_"
        exit 1
    }
}
else {
    Write-ColorOutput Green "✅ Virtual environment already exists"
}

Write-Output "Activating virtual environment..."
try {
    & .\env\Scripts\Activate.ps1
    if (!$?) {
        Write-ColorOutput Red "❌ Failed to activate virtual environment."
        exit 1
    }
}
catch {
    Write-ColorOutput Red "❌ Error activating virtual environment."
    Write-Output "You may need to run PowerShell as Administrator or enable script execution policy."
    Write-Output "Try running: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
    exit 1
}

Write-Output "Installing required packages (this may take a few minutes)..."
try {
    pip install --upgrade pip
    pip install -r requirements.txt
    if (!$?) {
        Write-ColorOutput Red "❌ Failed to install required packages."
        Write-Output "Check your internet connection and try again."
        exit 1
    }
    Write-ColorOutput Green "✅ Packages installed successfully"
}
catch {
    Write-ColorOutput Red "❌ Error installing packages: $_"
    exit 1
}

if (!(Test-Path -Path "yolov8n-pose.pt")) {
    Write-Output "Downloading pose detection model..."
    try {
        python -c "from ultralytics import YOLO; YOLO('yolov8n-pose.pt')"
        if (!$?) {
            Write-ColorOutput Red "❌ Failed to download pose model."
            exit 1
        }
        Write-ColorOutput Green "✅ Pose model downloaded successfully"
    }
    catch {
        Write-ColorOutput Red "❌ Error downloading pose model: $_"
        exit 1
    }
}
else {
    Write-ColorOutput Green "✅ Pose model already exists"
}

Write-Title "🎉 Setup completed successfully! Launching CVFit..."

try {
    python cvfit.py
}
catch {
    Write-ColorOutput Red "❌ Error launching CVFit: $_"
    exit 1
}

deactivate