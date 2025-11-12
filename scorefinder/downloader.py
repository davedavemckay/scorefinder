"""
File downloader utility for fetching music notation files from URLs.
"""

import logging
import requests
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, unquote

logger = logging.getLogger(__name__)


class FileDownloader:
    """Downloads files from URLs."""

    def __init__(self, timeout: int = 30):
        """
        Initialize the file downloader.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def download(self, url: str, output_path: Path) -> bool:
        """
        Download a file from a URL.

        Args:
            url: URL to download from
            output_path: Path to save the file

        Returns:
            True if download succeeded, False otherwise
        """
        logger.info(f"Downloading from: {url}")
        
        try:
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Downloaded to: {output_path}")
            return True
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return False

    def get_filename_from_url(self, url: str) -> str:
        """
        Extract filename from URL.

        Args:
            url: URL to extract filename from

        Returns:
            Filename string
        """
        # Try to get from Content-Disposition header
        try:
            response = self.session.head(url, timeout=10)
            if 'Content-Disposition' in response.headers:
                disposition = response.headers['Content-Disposition']
                if 'filename=' in disposition:
                    filename = disposition.split('filename=')[1].strip('"\'')
                    return unquote(filename)
        except Exception:
            pass
        
        # Fall back to parsing URL
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        filename = Path(path).name
        
        if not filename:
            filename = "downloaded_file"
        
        return filename

    def get_content(self, url: str) -> Optional[str]:
        """
        Get text content from a URL.

        Args:
            url: URL to fetch content from

        Returns:
            Content as string, or None if failed
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to get content from {url}: {e}")
            return None

    def get_binary_content(self, url: str) -> Optional[bytes]:
        """
        Get binary content from a URL.

        Args:
            url: URL to fetch content from

        Returns:
            Content as bytes, or None if failed
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to get content from {url}: {e}")
            return None
