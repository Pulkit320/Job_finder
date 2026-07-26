#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).parent.resolve()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

try:
    from cli.commands import app
except ModuleNotFoundError:
    from job_finder.cli.commands import app

if __name__ == "__main__":
    app()
