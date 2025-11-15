"""
Main application module for ScoreFinder.

Coordinates the search, conversion and verification of
drum notation files.
"""

import logging
from pathlib import Path
from typing import List, Optional
import sys
import subprocess
import shutil

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
                "Invalid configuration. Please ensure all required settings are "
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
        Find drum notation for a song, with interactive prompts for processing.
        """
        logger.info(f"Finding drum notation for: {song_name}" + 
                   (f" by {artist}" if artist else ""))
        
        # Step 1: Search for notation
        print(f"\n🔍 Searching for drum notation...")
        results = self.searcher.search_drum_notation(song_name, artist, failed_urls=self.failed_urls)
        
        if not results:
            print("❌ No new results found")
            return None
        
        print(f"✓ Found {len(results)} new results to process.")

        # Step 2: Interactively process results
        for i, result in enumerate(results, 1):
            print(f"\n{"-"*20}\n📄 Result {i}/{len(results)}: {result.title}")
            print(f"   Format: {result.file_format}, URL: {result.url}")

            temp_file_path, preview_path, start_page = self._get_preview(result, song_name)

            if preview_path:
                print(f"   🖼️  Displaying preview...")
                # Open preview with system default viewer
                if sys.platform == "win32":
                    os.startfile(preview_path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", preview_path])
                else:
                    subprocess.run(["xdg-open", preview_path])
            else:
                print("   ⚠️  Could not generate a preview for this format.")

            # Interactive prompt
            while True:
                choice = input("   ➡️  Choose an action: (P)roceed, (S)kip, (D)ownload Source, (Q)uit: ").lower()
                if choice in ['p', 's', 'd', 'q']:
                    break
                print("      Invalid choice, please try again.")

            if choice == 'q':
                print("\n🛑 Quitting.")
                return None
            elif choice == 's':
                print("   ⏭️  Skipping.")
                self._add_failed_url(result.url) # Add to failed list so we don't see it again
                continue
            elif choice == 'd':
                self._save_source_document(result, temp_file_path, song_name)
                # We still add to failed_urls so we don't re-process it next time
                self._add_failed_url(result.url)
                continue
            elif choice == 'p':
                print("   ⚙️  Proceeding with conversion and verification...")
                try:
                    # If config is set, save a copy of the source before processing
                    if config.save_intermediate:
                        print("   💾  Saving intermediate source file (as configured)...")
                        self._save_source_document(result, temp_file_path, song_name)

                    # Pass the downloaded file and start page to the processing method
                    file_path = self._process_result(result, song_name, temp_file_path, start_page)
                    if file_path:
                        print(f"\n🎉 Successfully saved to: {file_path}")
                        return file_path
                    else:
                        # If processing failed after proceeding, add to failed list
                        self._add_failed_url(result.url)
                except Exception as e:
                    logger.error(f"Error processing result {i}: {e}")
                    print(f"   ❌ Error: {e}")
                    self._add_failed_url(result.url)
                    continue
        
        print("\n❌ Could not process any results successfully")
        return None

    def _get_preview(self, result: SearchResult, song_name: str) -> tuple[Optional[Path], Optional[Path], int]:
        """Downloads a file and generates a preview if possible."""
        print("   Downloading for preview...")
        temp_file_path = self.downloader.download_file(result.url, config.temp_dir)
        if not temp_file_path:
            print("   ❌ Download failed.")
            return None, None, 0

        preview_path = None
        start_page = 0
        if result.file_format == 'pdf':
            preview_path, start_page = self.converter.get_pdf_preview_image(temp_file_path, song_name)
        
        return temp_file_path, preview_path, start_page

    def _save_source_document(self, result: SearchResult, temp_file_path: Optional[Path], song_name: str):
        """Saves a copy of the original source file to the output directory."""
        safe_name = "".join(c for c in song_name if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
        
        if temp_file_path and temp_file_path.exists():
            # It's a real file (like a PDF), so copy it
            ext = temp_file_path.suffix
            output_path = config.output_dir / f"{safe_name}_source{ext}"
            shutil.copy(temp_file_path, output_path) # Use copy instead of move
            print(f"   ✓ Source file saved to: {output_path}")
        else:
            # It's likely a webpage, save a link
            output_path = config.output_dir / f"{safe_name}_source_link.html"
            with open(output_path, 'w') as f:
                f.write(f'<!DOCTYPE html><html><head><title>Link</title></head><body><a href="{result.url}">Click here to open the original source</a></body></html>')
            print(f"   ✓ Source link saved to: {output_path}")

    def _process_result(self, result: SearchResult, song_name: str, temp_file_path: Optional[Path], start_page: int = 0) -> Optional[Path]:
        """
        Process a single search result using the already downloaded temp file.
        """
        if not temp_file_path:
            return None

        formats_to_convert = ['pdf', 'gp5', 'gp4', 'gpx', 'gp', 'ptb']
        direct_formats = ['musicxml', 'xml', 'mid', 'midi']

        if result.file_format in formats_to_convert:
            return self._convert_and_verify(result, song_name, temp_file_path, start_page)
        elif result.file_format in direct_formats:
            # For direct formats, the temp file is the final file.
            return self._download_and_verify(result, song_name, temp_file_path)
        else:
            logger.warning(f"Unsupported file format '{result.file_format}' for URL: {result.url}")
            print(f"   ⚠️ Unsupported format: {result.file_format}")
            return None

    def _download_and_verify(
        self,
        result: SearchResult,
        song_name: str,
        temp_file_path: Path
    ) -> Optional[Path]:
        """Verify a file that doesn't need conversion."""
        print(f"   Verifying {result.file_format}...")
        
        verification = self.verifier.verify_file(temp_file_path)
        
        if not verification.valid:
            print(f"   ❌ Verification failed: {verification.message}")
            temp_file_path.unlink() # Clean up temp file
            return None

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
        song_name: str,
        temp_file_path: Path,
        start_page: int = 0
    ) -> Optional[Path]:
        """Convert other formats to MusicXML and verify."""
        print(f"   Converting {result.file_format} to MusicXML...")
        
        # Convert (file is already downloaded)
        try:
            musicxml_content = self.converter.convert_to_musicxml(
                temp_file_path,
                result.file_format,
                song_name,
                start_page=start_page
            )
        except Exception as e:
            print(f"   ❌ Conversion failed: {e}")
            return None
        finally:
            # Clean up the original downloaded file
            if temp_file_path.exists():
                temp_file_path.unlink()

        if not musicxml_content:
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
