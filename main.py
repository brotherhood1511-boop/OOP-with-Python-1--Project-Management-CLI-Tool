"""Entry point: python main.py <command> [options]"""

import sys

from project_tracker.cli import main

if __name__ == "__main__":
    sys.exit(main())