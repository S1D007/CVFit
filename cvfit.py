#!/usr/bin/env python3

import sys
from gui.app import main

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error starting CVFit: {e}", file=sys.stderr)
        sys.exit(1)