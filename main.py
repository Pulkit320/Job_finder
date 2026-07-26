#!/usr/bin/env python3
import sys
from pathlib import Path

# Add parent directory and package directory to sys.path
root = Path(__file__).parent.resolve()
if str(root.parent) not in sys.path:
    sys.path.insert(0, str(root.parent))
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from job_finder.cli.commands import app

if __name__ == "__main__":
    app()
