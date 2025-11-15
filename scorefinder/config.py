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
        # Project root directory
        sfhome = os.environ.get("SFHOME")
        if not sfhome:
            raise ValueError("SFHOME environment variable must be set.")
        self.project_root = Path(sfhome)

        # Google API settings
        with open(os.path.expanduser('~/.scorefinder'), 'r') as config_f:
            self.gemini_api_key = ''
            self.google_search_api_key = ''
            self.google_search_engine_id = ''
            self.output_dir = self.project_root / "scores"
            self.temp_dir = self.project_root / "temp"
            self.log_level = 'INFO'
            self.minimum_measures = 20
            self.maximum_search_results = 10
            self.llm_model = 'gemini-1.5-flash-latest'
            self.save_intermediate = False

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
                            if k == 'MINIMUM_MEASURES':
                                self.minimum_measures = int(v)
                            if k == 'MAXIMUM_SEARCH_RESULTS':
                                self.maximum_search_results = int(v)
                            if k == 'LLM_MODEL':
                                self.llm_model = v
                            if k == 'SAVE_INTERMEDIATE':
                                self.save_intermediate = v.lower() in ('true', '1', 'yes')
        
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not all([self.gemini_api_key, self.google_search_api_key, self.google_search_engine_id]):
            print("Error: Missing Google API credentials in environment.")
            print("Please set GEMINI_API_KEY, GOOGLE_SEARCH_API_KEY, and GOOGLE_SEARCH_ENGINE_ID")
            return False
        if self.maximum_search_results <= 0 or self.maximum_search_results > 10:
            print("Error: MAXIMUM_SEARCH_RESULTS must be a positive integer between 1 and 10.")
            return False
        return True


# Global configuration instance
config = Config()
