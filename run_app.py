#!/usr/bin/env python3
"""
CVFit Application Launcher
This script ensures the application runs with the correct path configuration.
"""
import os
import sys
import subprocess

def main():
    # Ensure we're in the right directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Run the GUI app
    gui_script = os.path.join(project_root, 'gui', 'app.py')
    subprocess.run([sys.executable, gui_script])

if __name__ == "__main__":
    main()