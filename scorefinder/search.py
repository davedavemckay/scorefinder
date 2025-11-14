"""
Google Search integration for finding drum notation files.

Uses Google Custom Search API to find MusicXML, MIDI, and other
music notation files for drum scores.
"""

import logging
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

    def _detect_format(self, url: str) -> str:
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
    """Searches for drum notation files using Google Custom Search."""

    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        """
        Initialize the notation searcher.

        Args:
            api_key: Google Search API key (uses config if not provided)
        """
        self.api_key = api_key or config.google_search_api_key
        self.search_engine_id = search_engine_id or config.google_search_engine_id
        
        if not self.api_key:
            raise ValueError("Google API key is required")

    def search_drum_notation(self, song_name: str, artist: Optional[str] = None,
                            max_results: int = 10) -> List[SearchResult]:
        """
        Search for drum notation files for a given song.

        Args:
            song_name: Name of the song
            artist: Optional artist name to refine search
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        # Build search query
        query_parts = [song_name]
        if artist:
            query_parts.append(artist)
        query_parts.extend(["drum", "notation", "OR", "musicxml", "OR", "midi", "OR", "sheet music"])
        query = " ".join(query_parts)
        
        logger.info(f"Searching for: {query}")
        
        try:
            service = build("customsearch", "v1", developerKey=self.api_key)
            
            results = []
            page = 1
            
            while len(results) < max_results:
                start_index = (page - 1) * 10 + 1
                
                search_response = service.cse().list(
                    q=query,
                    cx=self.search_engine_id,
                    start=start_index,
                    num=min(10, max_results - len(results))
                ).execute()
                
                items = search_response.get('items', [])
                if not items:
                    break
                
                for item in items:
                    result = SearchResult(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        snippet=item.get('snippet', '')
                    )
                    results.append(result)
                
                # Check if there are more results
                if 'queries' not in search_response or 'nextPage' not in search_response['queries']:
                    break
                
                page += 1
            
            logger.info(f"Found {len(results)} results")
            return results[:max_results]
        
        except HttpError as e:
            logger.error(f"HTTP error during search: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise

    def filter_by_format(self, results: List[SearchResult], 
                        formats: List[str]) -> List[SearchResult]:
        """
        Filter search results by file format.

        Args:
            results: List of search results
            formats: List of formats to include (e.g., ['musicxml', 'midi'])

        Returns:
            Filtered list of search results
        """
        return [r for r in results if r.file_format in formats]
