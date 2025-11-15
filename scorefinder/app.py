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
        Process a single search result by downloading, converting (if needed), and verifying.

        Args:
            result: The SearchResult to process.
            song_name: The name of the song for naming the final file.

        Returns:
            The path to the final saved file, or None if processing fails.
        """
        formats_to_convert = ['pdf', 'gp5', 'gp4', 'gpx', 'gp', 'ptb']
        direct_formats = ['musicxml', 'xml', 'mid', 'midi']

        if result.file_format in formats_to_convert:
            return self._convert_and_verify(result, song_name)
        elif result.file_format in direct_formats:
            return self._download_and_verify(result, song_name)
        else:
            logger.warning(f"Unsupported file format '{result.file_format}' for URL: {result.url}")
            print(f"   ⚠️ Unsupported format: {result.file_format}")
            return None

    def _download_and_verify(
        self,
        result: SearchResult,
        song_name: str
    ) -> Optional[Path]:
        """Download and verify a file that doesn't need conversion."""
        print(f"   Downloading and verifying {result.file_format}...")
        
        temp_file_path = self.downloader.download_file(result.url, config.temp_dir)
        if not temp_file_path:
            print("   ❌ Download failed.")
            return None

        verification = self.verifier.verify_file(temp_file_path)
        
        if not verification.valid:
            print(f"   ❌ Verification failed: {verification.message}")
            temp_file_path.unlink() # Clean up temp file
            return None

        print("   ✓ Verified")
        
        # Create a clean filename
        safe_song_name = "".join(c for c in song_name if c.isalnum() or c in " -_").rstrip()
        final_filename = f"{safe_song_name}.{result.file_format}"
        final_path = config.output_dir / final_filename
        
        # Move the verified file to the output directory
        temp_file_path.rename(final_path)
        
        return final_path

    def _convert_and_verify(
        self,
        result: SearchResult,
        song_name: str
    ) -> Optional[Path]:
        """Convert other formats to MusicXML and verify."""
        print(f"   Converting {result.file_format} to MusicXML...")
        
        temp_file_path = self.downloader.download_file(result.url, config.temp_dir)
        if not temp_file_path:
            print("   ❌ Download failed.")
            return None
        
        # Convert
        try:
            musicxml_content = self.converter.convert_to_musicxml(
                temp_file_path,
                result.file_format
            )
        except Exception as e:
            print(f"   ❌ Conversion failed: {e}")
            temp_file_path.unlink() # Clean up temp file
            return None
        
        # Clean up the temporary file
        temp_file_path.unlink()

        if not musicxml_content:
            # Conversion failed, message is already printed by the converter
            return None
        
        print(f"   ✓ Converted to MusicXML")
        
        # Save the MusicXML content to a temporary file for verification
        temp_xml_path = config.temp_dir / f"{Path(temp_file_path).stem}.xml"
        with open(temp_xml_path, 'w', encoding='utf-8') as f:
            f.write(musicxml_content)

        # Verify content
        print(f"   Verifying...")
        verification = self.verifier.verify_file(temp_xml_path)
        
        if not verification.valid:
            print(f"   ❌ Verification failed: {verification.message}")
            temp_xml_path.unlink()
            return None
        
        # Check for minimum measure count
        if verification.details and 'measures' in verification.details and verification.details['measures'] < config.minimum_measures:
            print(f"   ❌ Verification failed: Score has fewer than {config.minimum_measures} measures.")
            temp_xml_path.unlink()
            return None

        print(f"   ✓ Verified")
        
        # Save to file
        safe_name = "".join(c for c in song_name if c.isalnum() or c in (' ', '-', '_'))
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}.musicxml"
        output_path = config.output_dir / filename
        
        temp_xml_path.rename(output_path)
        
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
