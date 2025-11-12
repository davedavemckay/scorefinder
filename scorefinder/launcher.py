"""
Musescore Studio launcher integration.

Opens verified music notation files in Musescore Studio for editing.
"""

import logging
import subprocess
import platform
from pathlib import Path
from typing import Optional

from .config import config

logger = logging.getLogger(__name__)


class MusescoreLauncher:
    """Launches Musescore Studio with music notation files."""

    def __init__(self, musescore_path: Optional[str] = None):
        """
        Initialize the Musescore launcher.

        Args:
            musescore_path: Path to Musescore executable (uses config if not provided)
        """
        self.musescore_path = musescore_path or config.musescore_path

    def launch(self, file_path: Path, wait: bool = False) -> bool:
        """
        Launch Musescore Studio with the specified file.

        Args:
            file_path: Path to the music notation file to open
            wait: Whether to wait for Musescore to close

        Returns:
            True if launched successfully, False otherwise
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False

        logger.info(f"Launching Musescore with file: {file_path}")

        try:
            # Build command based on platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Use 'open' command on macOS
                cmd = ["open", "-a", self.musescore_path, str(file_path)]
            else:
                # Windows and Linux
                cmd = [self.musescore_path, str(file_path)]
            
            # Launch Musescore
            if wait:
                result = subprocess.run(cmd, check=True)
                logger.info("Musescore closed")
                return result.returncode == 0
            else:
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                logger.info("Musescore launched")
                return True

        except FileNotFoundError:
            logger.error(f"Musescore not found at: {self.musescore_path}")
            logger.error("Please install Musescore Studio or set the correct path in .env")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Error launching Musescore: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error launching Musescore: {e}")
            return False

    def is_available(self) -> bool:
        """
        Check if Musescore is available at the configured path.

        Returns:
            True if Musescore is available, False otherwise
        """
        if not self.musescore_path:
            return False
        
        # Check if path exists
        path = Path(self.musescore_path)
        if path.exists() and path.is_file():
            return True
        
        # Try to run which/where command
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["where", self.musescore_path],
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    ["which", self.musescore_path],
                    capture_output=True,
                    text=True
                )
            return result.returncode == 0
        except Exception:
            return False
