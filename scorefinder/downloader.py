"""
File downloader utility for fetching music notation files from URLs.
"""

import logging
from pathlib import Path
from typing import Optional
import requests

logger = logging.getLogger(__name__)

class FileDownloader:
    """Handles downloading files from URLs."""

    def download_file(self, url: str, destination_folder: Path) -> Optional[Path]:
        """
        Download a file from a URL.

        Args:
            url: The URL to download from.
            destination_folder: The folder to save the file in.

        Returns:
            The path to the downloaded file, or None if download fails.
        """
        try:
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()

            # Verify content type
            content_type = response.headers.get('Content-Type', '').lower()
            file_extension = Path(url).suffix.lower()

            if file_extension == '.pdf' and 'application/pdf' not in content_type:
                logger.warning(f"Expected PDF, but got Content-Type: {content_type} for {url}")
                return None
            
            if file_extension in ['.gp5', '.gpx', '.gp'] and 'application/octet-stream' not in content_type and 'application/x-guitar-pro' not in content_type:
                 logger.warning(f"Expected Guitar Pro, but got Content-Type: {content_type} for {url}")
                 # We are more lenient with GP files as servers often mislabel them.

            # Create a safe filename
            filename = Path(url.split('/')[-1]).name
            destination_path = destination_folder / filename

            with open(destination_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded {url} to {destination_path}")
            return destination_path

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            return None
