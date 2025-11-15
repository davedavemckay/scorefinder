"""
Google Search integration for finding drum notation files.

Uses Google Custom Search API to find MusicXML, MIDI, and other
music notation files for drum scores.
"""

import logging
from typing import List, Optional, Set

from googleapiclient.discovery import build

from .config import config

logger = logging.getLogger(__name__)


class SearchResult:
    """Represents a search result for a music notation file."""

    def __init__(self, title: str, url: str, snippet: str, file_format: Optional[str] = None):
        """
        Initialize a search result.

        Args:
            title: Title of the search result
            url: URL of the file or page
            snippet: Description snippet from the search result
            file_format: Detected file format (musicxml, midi, pdf, etc.)
        """
        self.title = title
        self.url = url
        self.snippet = snippet
        self.file_format = file_format or self._detect_format(url)

    @staticmethod
    def _detect_format(url: str) -> str:
        """Detect file format from URL."""
        url_lower = url.lower()
        if url_lower.endswith(('.xml', '.musicxml', '.mxl')):
            return 'musicxml'
        elif url_lower.endswith(('.mid', '.midi')):
            return 'midi'
        elif url_lower.endswith('.pdf'):
            return 'pdf'
        elif url_lower.endswith('.abc'):
            return 'abc'
        elif url_lower.endswith('.gp'):
            return 'guitar-pro'
        else:
            return 'unknown'

    def __repr__(self) -> str:
        return f"SearchResult(title='{self.title}', format='{self.file_format}')"


class NotationSearcher:
    """Performs searches for drum notation."""

    def search_drum_notation(
        self,
        song_name: str,
        artist: Optional[str] = None,
        failed_urls: Optional[Set[str]] = None
    ) -> List[SearchResult]:
        """
        Search for drum notation using Google Custom Search API.

        Args:
            song_name: Name of the song
            artist: Optional artist name
            failed_urls: A set of URLs to skip.

        Returns:
            A list of SearchResult objects.
        """
        if artist:
            logger.info(f"Searching for '{song_name}' by '{artist}'")
        else:
            logger.info(f"Searching for '{song_name}'")

        query = f'"{song_name}" "{artist}" drum score OR drum notation OR drum sheet music filetype:pdf OR filetype:gp5 OR filetype:gp4 OR filetype:gpx OR filetype:gp OR filetype:ptb OR filetype:musicxml OR filetype:xml OR filetype:mid'
        
        valid_results: List[SearchResult] = []
        processed_urls = set()
        if failed_urls:
            processed_urls.update(failed_urls)
        
        start_index = 1
        num_to_fetch = config.maximum_search_results
        
        try:
            service = build("customsearch", "v1", developerKey=config.google_search_api_key)
            
            while len(valid_results) < config.maximum_search_results:
                res = service.cse().list(
                    q=query,
                    cx=config.google_search_engine_id,
                    num=num_to_fetch,
                    start=start_index
                ).execute()

                items = res.get('items', [])
                if not items:
                    # No more results from the API
                    break

                for item in items:
                    url = item.get('link')
                    if not url or url in processed_urls:
                        continue

                    processed_urls.add(url)
                    
                    result = SearchResult(
                        title=item.get('title', 'No Title'),
                        url=url,
                        snippet=item.get('snippet', ''),
                        file_format=self._guess_format(url, item.get('fileFormat', ''))
                    )
                    valid_results.append(result)

                    if len(valid_results) >= config.maximum_search_results:
                        break
                
                start_index += len(items)
                # In case the API returns fewer than requested, we don't want to get stuck in a loop
                if len(items) < num_to_fetch:
                    break

            return valid_results

        except Exception as e:
            logger.error(f"An error occurred during search: {e}")
            print(f"❌ An error occurred during search: {e}")
            return []

    def _guess_format(self, url: str, file_format_hint: str) -> str:
        """Guess the file format from URL and hint."""
        format_from_url = SearchResult._detect_format(url)
        if format_from_url != 'unknown':
            return format_from_url
        return file_format_hint if file_format_hint in ['musicxml', 'midi', 'pdf', 'abc', 'guitar-pro'] else 'unknown'
