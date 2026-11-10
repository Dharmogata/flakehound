"""Module entry point for `python -m flakehound`."""

import sys

from flakehound.cli import main

if __name__ == "__main__":
    sys.exit(main())
