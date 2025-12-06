#!/usr/bin/env python3
"""
Entry point for the core CLI module.

This allows the CLI to be run as:
python -m core
"""

from .cli.main import main

if __name__ == '__main__':
    main()