"""
Main application module for ScoreFinder.

Coordinates the search, conversion, verification, and launching of
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
from .launcher import MusescoreLauncher
from .downloader import FileDownloader

logger = logging.getLogger(__name__)


class ScoreFinder:
    """Main application class for finding and processing drum notation."""

    def __init__(self):
        """Initialize ScoreFinder with all required components."""
        # Validate configuration
        if not config.validate():
            raise ValueError(
                "Invalid configuration. Please ensure GOOGLE_API_KEY and "
                "GOOGLE_SEARCH_ENGINE_ID are set in .env file"
            )
        
        self.searcher = NotationSearcher()
        self.converter = FormatConverter()
        self.verifier = MusicVerifier()
        self.launcher = MusescoreLauncher()
        self.downloader = FileDownloader()

    def find_and_open_notation(
        self,
        song_name: str,
        artist: Optional[str] = None,
        auto_open: bool = True
    ) -> Optional[Path]:
        """
        Find drum notation for a song and open it in Musescore.

        Args:
            song_name: Name of the song
            artist: Optional artist name
            auto_open: Whether to automatically open in Musescore

        Returns:
            Path to the saved notation file, or None if failed
        """
        logger.info(f"Finding drum notation for: {song_name}" + 
                   (f" by {artist}" if artist else ""))
        
        # Step 1: Search for notation
        print(f"\n🔍 Searching for drum notation...")
        results = self.searcher.search_drum_notation(song_name, artist)
        
        if not results:
            print("❌ No results found")
            return None
        
        print(f"✓ Found {len(results)} results")
        
        # Step 2: Process results
        for i, result in enumerate(results, 1):
            print(f"\n📄 Result {i}/{len(results)}: {result.title}")
            print(f"   Format: {result.file_format}")
            print(f"   URL: {result.url}")
            
            try:
                file_path = self._process_result(result, song_name)
                
                if file_path:
                    print(f"\n✓ Successfully saved to: {file_path}")
                    
                    if auto_open:
                        print(f"\n🎵 Opening in Musescore Studio...")
                        if self.launcher.launch(file_path):
                            print("✓ Musescore launched successfully")
                        else:
                            print("⚠ Failed to launch Musescore")
                            print(f"   Please open the file manually: {file_path}")
                    
                    return file_path
            
            except Exception as e:
                logger.error(f"Error processing result {i}: {e}")
                print(f"   ❌ Error: {e}")
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
        Search and list results without downloading.

        Args:
            song_name: Name of the song
            artist: Optional artist name

        Returns:
            List of search results
        """
        print(f"\n🔍 Searching for drum notation...")
        results = self.searcher.search_drum_notation(song_name, artist)
        
        if not results:
            print("❌ No results found")
            return []
        
        print(f"\n✓ Found {len(results)} results:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   Format: {result.file_format}")
            print(f"   URL: {result.url}")
            print(f"   {result.snippet[:100]}...")
            print()
        
        return results
