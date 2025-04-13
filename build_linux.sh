#!/bin/bash
# CVFit Linux Build Script

echo "========================================================="
echo "          Building CVFit for Linux                       "
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

echo "Building CVFit executable..."
pyinstaller cvfit.spec

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

if command -v appimagetool &> /dev/null; then
    echo "Creating AppImage..."
    
    mkdir -p AppDir/usr/{bin,share/{applications,icons/hicolor/256x256/apps}}
    cp -r dist/CVFit/* AppDir/usr/bin/
    
    cat > AppDir/usr/share/applications/cvfit.desktop << EOF
[Desktop Entry]
Name=CVFit
Exec=CVFit
Icon=cvfit
Type=Application
Categories=Utility;
Terminal=false
EOF

    if [ -f "resources/icon.png" ]; then
        cp resources/icon.png AppDir/usr/share/icons/hicolor/256x256/apps/cvfit.png
    else
        convert -size 256x256 xc:transparent \
                -font Helvetica -pointsize 72 -fill black -gravity center \
                -annotate 0 "CVFit" AppDir/usr/share/icons/hicolor/256x256/apps/cvfit.png || \
        echo "⚠️ Failed to create icon (ImageMagick not installed?)"
    fi
    
    cat > AppDir/AppRun << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
exec usr/bin/CVFit "\$@"
EOF
    chmod +x AppDir/AppRun
    
    ARCH=x86_64 appimagetool AppDir dist/CVFit-1.0.0-x86_64.AppImage
    
    rm -rf AppDir
    
    echo "✅ AppImage created: dist/CVFit-1.0.0-x86_64.AppImage"
else
    echo "⚠️ appimagetool not found, skipping AppImage creation"
    echo "If you want to create an AppImage, install appimagetool:"
    echo "    wget -O appimagetool https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    echo "    chmod +x appimagetool"
    echo "    sudo mv appimagetool /usr/local/bin/"
    
    echo "Creating tarball instead..."
    cd dist
    tar -czvf CVFit-1.0.0-linux.tar.gz CVFit
    cd ..
    echo "✅ Tarball created: dist/CVFit-1.0.0-linux.tar.gz"
fi

echo "========================================================="
echo "✅ Build completed successfully! Output is in dist folder."
echo "Distribution options:"
echo "   - dist/CVFit/: standalone application folder"
if [ -f "dist/CVFit-1.0.0-x86_64.AppImage" ]; then
    echo "   - dist/CVFit-1.0.0-x86_64.AppImage: portable AppImage"
fi
if [ -f "dist/CVFit-1.0.0-linux.tar.gz" ]; then
    echo "   - dist/CVFit-1.0.0-linux.tar.gz: compressed tarball"
fi
echo "========================================================="