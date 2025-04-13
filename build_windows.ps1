# CVFit Windows Build Script

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

Write-Title "Building CVFit for Windows"

if (-not (Test-Path -Path "resources")) {
    New-Item -ItemType Directory -Path "resources"
    Write-Output "Created resources directory"
}

if (Test-Path -Path "env") {
    & .\env\Scripts\Activate.ps1
    Write-ColorOutput Green "✅ Activated virtual environment"
}
else {
    Write-Output "⚠️ Virtual environment not found, creating one..."
    python -m venv env
    & .\env\Scripts\Activate.ps1
    pip install --upgrade pip
    pip install -r requirements.txt
    Write-ColorOutput Green "✅ Virtual environment created and activated"
}

if (-not (Test-Path -Path "yolov8n-pose.pt")) {
    Write-Output "⚠️ YOLOv8 model not found, downloading..."
    python -c "from ultralytics import YOLO; YOLO('yolov8n-pose.pt')"
    Write-ColorOutput Green "✅ Model downloaded"
}

Write-Output "Cleaning previous build files..."
if (Test-Path -Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path -Path "dist") { Remove-Item -Recurse -Force "dist" }

Write-Output "Building CVFit executable..."
pyinstaller cvfit.spec

if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "❌ Build failed"
    exit 1
}

Write-Output "Checking for NSIS installation for creating installer..."
$nsisPath = "C:\Program Files (x86)\NSIS\makensis.exe"
if (Test-Path $nsisPath) {
    Write-Output "Creating installer with NSIS..."
    
    $nsisScript = @"
!include "MUI2.nsh"

; Application details
Name "CVFit"
OutFile "dist\CVFit-1.0.0-setup.exe"
InstallDir "\$PROGRAMFILES\CVFit"

; Modern interface settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "\$INSTDIR"
  File /r "dist\CVFit\*.*"
  
  ; Create shortcut
  CreateDirectory "\$SMPROGRAMS\CVFit"
  CreateShortCut "\$SMPROGRAMS\CVFit\CVFit.lnk" "\$INSTDIR\CVFit.exe"
  CreateShortCut "\$DESKTOP\CVFit.lnk" "\$INSTDIR\CVFit.exe"
  
  ; Write uninstaller
  WriteUninstaller "\$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "\$INSTDIR\Uninstall.exe"
  RMDir /r "\$INSTDIR"
  Delete "\$SMPROGRAMS\CVFit\CVFit.lnk"
  RMDir "\$SMPROGRAMS\CVFit"
  Delete "\$DESKTOP\CVFit.lnk"
SectionEnd
"@

    $nsisScript | Out-File -FilePath "installer.nsi" -Encoding ASCII
    & $nsisPath "installer.nsi"
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput Green "✅ Installer created successfully: dist\CVFit-1.0.0-setup.exe"
    } else {
        Write-ColorOutput Yellow "⚠️ Failed to create installer"
    }
    
    Remove-Item "installer.nsi"
} else {
    Write-Output "NSIS not found. Skipping installer creation."
    Write-Output "If you want to create an installer, install NSIS from https://nsis.sourceforge.io/"
    
    Write-Output "Creating ZIP archive instead..."
    Compress-Archive -Path "dist\CVFit\*" -DestinationPath "dist\CVFit-1.0.0-windows.zip" -Force
    Write-ColorOutput Green "✅ ZIP archive created: dist\CVFit-1.0.0-windows.zip"
}

Write-Title "Build completed successfully! Output is in dist folder."
Write-Output "Distribution options:"
Write-Output "   - dist\CVFit\: standalone application folder"
if (Test-Path "dist\CVFit-1.0.0-setup.exe") {
    Write-Output "   - dist\CVFit-1.0.0-setup.exe: installer package"
} 
if (Test-Path "dist\CVFit-1.0.0-windows.zip") {
    Write-Output "   - dist\CVFit-1.0.0-windows.zip: zipped application"
}