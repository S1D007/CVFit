# Installation

## Prerequisites

Before installing CVFit, ensure you have the following:

- Python 3.8 or higher
- A webcam or video input device
- Sufficient disk space for model files (~50MB)
- Recommended: GPU with CUDA support for better performance

## Installation Methods

### Method 1: From PyPI (Recommended)

```bash
pip install cvfit
```

### Method 2: From Source

```bash
# Clone the repository
git clone https://github.com/s1d007/CVFit.git
cd CVFit

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Method 3: Using Docker

```bash
# Pull the image
docker pull s1d007/cvfit:latest

# Or build from source
docker build -t cvfit .
```

## Post-Installation

After installation, download the required model files:

```bash
# Automatically download required model files
python download_model.py
```

## Platform-Specific Instructions

### Windows

Run the setup script:

```powershell
.\setup.ps1
```

### macOS

Run the setup script:

```bash
./setup.sh
```

### Linux

Run the setup script:

```bash
./setup.sh
```

## Verification

Verify your installation by running:

```bash
python -c "import cvfit; print(cvfit.__version__)"
```

You should see the installed version number printed.

## Troubleshooting

If you encounter issues:

1. Check that all dependencies are installed
2. Ensure your webcam is properly connected and accessible
3. Verify that the model files are downloaded correctly
4. For GPU acceleration, ensure CUDA is properly set up
