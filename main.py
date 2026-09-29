"""MPR-automation entry point: python main.py"""
import sys

from app.bootstrap import run

if __name__ == "__main__":
    sys.exit(run())
