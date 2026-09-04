#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.32",
#   "mutagen>=1.47",
#   "python-dotenv>=1.0",
# ]
# ///
"""Compatibility entrypoint for the Volcengine ASR 2.0 standard workflow."""

from transcribe import main


if __name__ == "__main__":
    main()
