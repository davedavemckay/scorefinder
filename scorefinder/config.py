"""
Configuration management for ScoreFinder.

Loads configuration from environment variables and provides
access to application settings.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .scorefinder file
load_dotenv(os.path.expanduser("~/.scorefinder"))


class Config:
    """Application configuration."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Google API settings
        with open(os.path.expanduser('~/.scorefinder'), 'r') as config_f:
            self.gemini_api_key = ''
            self.google_search_api_key = ''
            self.google_search_engine_id = ''
            self.output_dir = Path(os.environ.get("SFHOME") + "/scores")
            self.temp_dir = Path(os.environ.get("SFHOME") + "/temp")
            self.log_level = 'INFO'

            for line in config_f.readlines():
                if len(line) == 0:
                    continue
                if not line.strip().startswith('#'):
                    if '=' in line:
                        if len(line.split('=')) == 2:
                            k, v = (x.strip() for x in line.split('='))
                            if k == 'GOOGLE_SEARCH_API_KEY':
                                self.google_search_api_key = v
                            if k == 'GOOGLE_SEARCH_ENGINE_ID':
                                self.google_search_engine_id = v
                            if k == 'GEMINI_API_KEY':
                                self.gemini_api_key = v
                            if k == 'OUTPUT_DIR':
                                self.output_dir = Path(v)
                            if k == 'TEMP_DIR':
                                self.temp_dir = Path(v)
                            if k == 'LOG_LEVEL':
                                self.log_level = v
        
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not all([self.gemini_api_key, self.google_search_api_key, self.google_search_engine_id]):
            print("Error: Missing Google API credentials in environment.")
            print("Please set GEMINI_API_KEY, GOOGLE_SEARCH_API_KEY, and GOOGLE_SEARCH_ENGINE_ID")
            return False
        return True


# Global configuration instance
config = Config()
