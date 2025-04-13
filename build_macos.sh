#!/bin/bash
# CVFit macOS Build Script

echo "========================================================="
echo "          Building CVFit for macOS                       "
echo "========================================================="

if [ ! -d "resources" ]; then
    mkdir resources
    echo "Created resources directory"
fi

if [ -d "env" ]; then
    source env/bin/activate
    echo "✅ Activated virtual environment"
else
    echo "⚠️ Virtual environment not found, creating one..."
    python3 -m venv env
    source env/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Virtual environment created and activated"
fi

if [ ! -f "yolov8n-pose.pt" ]; then
    echo "⚠️ YOLOv8 model not found, downloading..."
    python -c "from ultralytics import YOLO; YOLO('yolov8n-pose.pt')"
    echo "✅ Model downloaded"
fi

echo "Cleaning previous build files..."
rm -rf build dist

echo "Building CVFit.app..."
pyinstaller cvfit.spec

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "Creating DMG file..."
mkdir -p dist/CVFit-dmg
cp -r "dist/CVFit.app" dist/CVFit-dmg/
create-dmg \
    --volname "CVFit Installer" \
    --volicon "resources/icon.icns" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "CVFit.app" 200 190 \
    --hide-extension "CVFit.app" \
    --app-drop-link 600 185 \
    "dist/CVFit-1.0.0.dmg" \
    "dist/CVFit-dmg/" || echo "⚠️ create-dmg failed. If not installed, run 'brew install create-dmg'"

echo "========================================================="
echo "✅ Build completed successfully! Output is in dist folder."
echo "   - CVFit.app: standalone application bundle"
echo "   - CVFit-1.0.0.dmg: disk image for distribution (if create-dmg was installed)"
echo "========================================================="

echo "You can distribute the .app directly or use the .dmg installer."