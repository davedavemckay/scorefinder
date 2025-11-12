"""
Configuration management for ScoreFinder.

Loads configuration from environment variables and provides
access to application settings.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Google API settings
        self.google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
        self.google_search_engine_id: Optional[str] = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        # Musescore settings
        self.musescore_path: str = os.getenv("MUSESCORE_PATH", self._detect_musescore())
        
        # Application directories
        self.output_dir: Path = Path(os.getenv("OUTPUT_DIR", "./scores"))
        self.temp_dir: Path = Path(os.getenv("TEMP_DIR", "./temp"))
        
        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _detect_musescore(self) -> str:
        """Attempt to detect Musescore installation."""
        import platform
        system = platform.system()
        
        possible_paths = []
        if system == "Windows":
            possible_paths = [
                r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe",
                r"C:\Program Files (x86)\MuseScore 4\bin\MuseScore4.exe",
                r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe",
            ]
        elif system == "Darwin":  # macOS
            possible_paths = [
                "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
                "/Applications/MuseScore 3.app/Contents/MacOS/mscore",
            ]
        else:  # Linux
            possible_paths = [
                "/usr/bin/mscore",
                "/usr/local/bin/mscore",
                "/usr/bin/musescore",
            ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return "mscore"  # Default, hope it's in PATH

    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not self.google_api_key:
            return False
        if not self.google_search_engine_id:
            return False
        return True


# Global configuration instance
config = Config()
