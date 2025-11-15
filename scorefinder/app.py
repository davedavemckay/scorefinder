"""
Main application module for ScoreFinder.

Coordinates the search, conversion and verification of
drum notation files.
"""

import logging
from pathlib import Path
from typing import List, Optional
import sys

from .config import config
from .search import NotationSearcher, SearchResult
from .converter import FormatConverter
from .verifier import MusicVerifier
from .downloader import FileDownloader

logger = logging.getLogger(__name__)


class ScoreFinder:
    """Main application class for finding and processing drum notation."""

    def __init__(self):
        """Initialize ScoreFinder with all required components."""
        # Validate configuration
        if not config.validate():
            raise ValueError(
                "Invalid configuration. Please ensure GOOGLE_API_JSON is "
                "set in .scorefinder file"
            )
        
        self.searcher = NotationSearcher()
        self.converter = FormatConverter()
        self.verifier = MusicVerifier()
        self.downloader = FileDownloader()
        self.failed_urls_file = config.project_root / "failed_urls.txt"
        self.failed_urls = self._load_failed_urls()

    def _load_failed_urls(self) -> set[str]:
        """Load failed URLs from the data file."""
        if not self.failed_urls_file.exists():
            return set()
        with open(self.failed_urls_file, 'r', encoding='utf-8') as f:
            return {line.strip() for line in f if line.strip()}

    def _add_failed_url(self, url: str):
        """Add a URL to the failed list and save it to the file."""
        if url not in self.failed_urls:
            self.failed_urls.add(url)
            with open(self.failed_urls_file, 'a', encoding='utf-8') as f:
                f.write(f"{url}\n")
            logger.info(f"Added failed URL to list: {url}")

    def find_notation(
        self,
        song_name: str,
        artist: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Find drum notation for a song.

        Args:
            song_name: Name of the song
            artist: Optional artist name

        Returns:
            Path to the saved notation file, or None if failed
        """
        logger.info(f"Finding drum notation for: {song_name}" + 
                   (f" by {artist}" if artist else ""))
        
        # Step 1: Search for notation
        print(f"\n🔍 Searching for drum notation...")
        results = self.searcher.search_drum_notation(song_name, artist, failed_urls=self.failed_urls)
        
        if not results:
            print("❌ No results found")
            return None
        
        print(f"✓ Found {len(results)} new results to process.")

        if not results:
            return None
        
        # Step 2: Process results
        for i, result in enumerate(results, 1):
            print(f"\n📄 Result {i}/{len(results)}: {result.title}")
            print(f"   Format: {result.file_format}")
            print(f"   URL: {result.url}")
            
            try:
                file_path = self._process_result(result, song_name)
                
                if file_path:
                    print(f"\n✓ Successfully saved to: {file_path}")
                    
                    return file_path
                else:
                    # If processing failed, add URL to failed list
                    self._add_failed_url(result.url)
            
            except Exception as e:
                logger.error(f"Error processing result {i}: {e}")
                print(f"   ❌ Error: {e}")
                self._add_failed_url(result.url)
                continue
        
        print("\n❌ Could not process any results successfully")
        return None

    def _process_result(self, result: SearchResult, song_name: str) -> Optional[Path]:
        """
        Process a single search result.

        Args:
            result: Search result to process
            song_name: Name of the song (for filename)

        Returns:
            Path to saved file, or None if processing failed
        """
        # Handle based on format
        if result.file_format in ['musicxml', 'midi']:
            return self._download_and_verify(result, song_name)
        else:
            return self._convert_and_verify(result, song_name)

    def _download_and_verify(
        self,
        result: SearchResult,
        song_name: str
    ) -> Optional[Path]:
        """Download and verify a MusicXML or MIDI file."""
        print(f"   Downloading {result.file_format} file...")
        
        # Determine file extension
        if result.file_format == 'musicxml':
            ext = '.musicxml'
        elif result.file_format == 'midi':
            ext = '.mid'
        else:
            ext = '.xml'
        
        # Create filename
        safe_name = "".join(c for c in song_name if c.isalnum() or c in (' ', '-', '_'))
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}{ext}"
        output_path = config.output_dir / filename
        
        # Download
        if not self.downloader.download(result.url, output_path):
            print(f"   ❌ Download failed")
            return None
        
        print(f"   ✓ Downloaded")
        
        # Verify
        print(f"   Verifying...")
        verification = self.verifier.verify_file(output_path)
        
        if verification.valid:
            print(f"   ✓ Verified: {verification.message}")
            if verification.details:
                # Check for minimum measure count
                if 'measures' in verification.details and verification.details['measures'] < 30:
                    measure_count = verification.details['measures']
                    print(f"   ❌ Verification failed: Score is too short ({measure_count} measures). Minimum is 20.")
                    if output_path.exists():
                        output_path.unlink()
                    return None

                for key, value in verification.details.items():
                    print(f"      {key}: {value}")
            return output_path
        else:
            print(f"   ❌ Verification failed: {verification.message}")
            # Clean up invalid file
            if output_path.exists():
                output_path.unlink()
            return None

    def _convert_and_verify(
        self,
        result: SearchResult,
        song_name: str
    ) -> Optional[Path]:
        """Convert other formats to MusicXML and verify."""
        print(f"   Converting {result.file_format} to MusicXML...")
        
        # Get content
        content = self.downloader.get_content(result.url)
        if not content:
            print(f"   ❌ Could not fetch content")
            return None
        
        # Convert
        try:
            musicxml_content = self.converter.convert_to_musicxml(
                content,
                result.file_format
            )
        except Exception as e:
            print(f"   ❌ Conversion failed: {e}")
            return None
        
        print(f"   ✓ Converted to MusicXML")
        
        # Verify content
        print(f"   Verifying...")
        verification = self.verifier.verify_content(musicxml_content, 'musicxml')
        
        if not verification.valid:
            print(f"   ❌ Verification failed: {verification.message}")
            return None
        
        # Check for minimum measure count
        if verification.details and 'measures' in verification.details and verification.details['measures'] < config.minimum_measures:
            print(f"   ❌ Verification failed: Score has fewer than {config.minimum_measures} measures.")
            return None

        print(f"   ✓ Verified")
        
        # Save to file
        safe_name = "".join(c for c in song_name if c.isalnum() or c in (' ', '-', '_'))
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}_converted.musicxml"
        output_path = config.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(musicxml_content)
        
        # Verify saved file
        final_verification = self.verifier.verify_file(output_path)
        if not final_verification.valid:
            print(f"   ❌ Final verification failed: {final_verification.message}")
            if output_path.exists():
                output_path.unlink()
            return None
        
        return output_path

    def list_results(
        self,
        song_name: str,
        artist: Optional[str] = None
    ) -> List[SearchResult]:
        """
        List search results without processing them.

        Args:
            song_name: Name of the song
            artist: Optional artist name

        Returns:
            A list of SearchResult objects.
        """
        print(f"\n🔍 Searching for drum notation...")
        results = self.searcher.search_drum_notation(song_name, artist, failed_urls=self.failed_urls)
        
        if not results:
            print("❌ No new results found")
            return []
        
        print(f"\n✓ Found {len(results)} new results:\n")

        if not results:
            return []
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   Format: {result.file_format}")
            print(f"   URL: {result.url}")
            print(f"   {result.snippet[:100]}...")
            print()
        
        return results
