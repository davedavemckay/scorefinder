"""
Basic tests for ScoreFinder modules.
"""

import unittest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestImports(unittest.TestCase):
    """Test that all modules can be imported."""

    def test_import_package(self):
        """Test importing the main package."""
        import scorefinder
        self.assertEqual(scorefinder.__version__, "0.1.0")

    def test_import_config(self):
        """Test importing config module."""
        from scorefinder import config
        self.assertIsNotNone(config)

    def test_import_search(self):
        """Test importing search module."""
        from scorefinder.search import NotationSearcher, SearchResult
        self.assertIsNotNone(NotationSearcher)
        self.assertIsNotNone(SearchResult)

    def test_import_converter(self):
        """Test importing converter module."""
        from scorefinder.converter import FormatConverter
        self.assertIsNotNone(FormatConverter)

    def test_import_verifier(self):
        """Test importing verifier module."""
        from scorefinder.verifier import MusicVerifier, VerificationResult
        self.assertIsNotNone(MusicVerifier)
        self.assertIsNotNone(VerificationResult)

    def test_import_launcher(self):
        """Test importing launcher module."""
        from scorefinder.launcher import MusescoreLauncher
        self.assertIsNotNone(MusescoreLauncher)

    def test_import_downloader(self):
        """Test importing downloader module."""
        from scorefinder.downloader import FileDownloader
        self.assertIsNotNone(FileDownloader)

    def test_import_app(self):
        """Test importing app module."""
        from scorefinder.app import ScoreFinder
        self.assertIsNotNone(ScoreFinder)


class TestSearchResult(unittest.TestCase):
    """Test SearchResult class."""

    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        from scorefinder.search import SearchResult
        
        result = SearchResult(
            title="Test Song",
            url="https://example.com/test.musicxml",
            snippet="Test snippet"
        )
        
        self.assertEqual(result.title, "Test Song")
        self.assertEqual(result.url, "https://example.com/test.musicxml")
        self.assertEqual(result.snippet, "Test snippet")
        self.assertEqual(result.file_format, "musicxml")

    def test_format_detection_musicxml(self):
        """Test MusicXML format detection."""
        from scorefinder.search import SearchResult
        
        result = SearchResult(
            title="Test",
            url="https://example.com/song.xml",
            snippet=""
        )
        self.assertEqual(result.file_format, "musicxml")

    def test_format_detection_midi(self):
        """Test MIDI format detection."""
        from scorefinder.search import SearchResult
        
        result = SearchResult(
            title="Test",
            url="https://example.com/song.mid",
            snippet=""
        )
        self.assertEqual(result.file_format, "midi")

    def test_format_detection_pdf(self):
        """Test PDF format detection."""
        from scorefinder.search import SearchResult
        
        result = SearchResult(
            title="Test",
            url="https://example.com/song.pdf",
            snippet=""
        )
        self.assertEqual(result.file_format, "pdf")


class TestVerificationResult(unittest.TestCase):
    """Test VerificationResult class."""

    def test_verification_result_valid(self):
        """Test creating a valid VerificationResult."""
        from scorefinder.verifier import VerificationResult
        
        result = VerificationResult(True, "Valid file")
        
        self.assertTrue(result.valid)
        self.assertEqual(result.message, "Valid file")
        self.assertTrue(result)  # Test __bool__

    def test_verification_result_invalid(self):
        """Test creating an invalid VerificationResult."""
        from scorefinder.verifier import VerificationResult
        
        result = VerificationResult(False, "Invalid file")
        
        self.assertFalse(result.valid)
        self.assertEqual(result.message, "Invalid file")
        self.assertFalse(result)  # Test __bool__

    def test_verification_result_with_details(self):
        """Test VerificationResult with details."""
        from scorefinder.verifier import VerificationResult
        
        details = {"parts": 1, "measures": 10}
        result = VerificationResult(True, "Valid", details)
        
        self.assertEqual(result.details["parts"], 1)
        self.assertEqual(result.details["measures"], 10)


class TestMusicVerifier(unittest.TestCase):
    """Test MusicVerifier class."""

    def test_verifier_creation(self):
        """Test creating a MusicVerifier."""
        from scorefinder.verifier import MusicVerifier
        
        verifier = MusicVerifier()
        self.assertIsNotNone(verifier)

    def test_verify_musicxml_content_valid(self):
        """Test verifying valid MusicXML content."""
        from scorefinder.verifier import MusicVerifier
        
        verifier = MusicVerifier()
        
        # Simple valid MusicXML
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1">
      <part-name>Drums</part-name>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
      </attributes>
    </measure>
  </part>
</score-partwise>'''
        
        result = verifier.verify_content(content, 'musicxml')
        self.assertTrue(result.valid)

    def test_verify_musicxml_content_invalid(self):
        """Test verifying invalid MusicXML content."""
        from scorefinder.verifier import MusicVerifier
        
        verifier = MusicVerifier()
        
        # Invalid XML
        content = '<invalid>Not valid MusicXML</invalid>'
        
        result = verifier.verify_content(content, 'musicxml')
        self.assertFalse(result.valid)


class TestFileDownloader(unittest.TestCase):
    """Test FileDownloader class."""

    def test_downloader_creation(self):
        """Test creating a FileDownloader."""
        from scorefinder.downloader import FileDownloader
        
        downloader = FileDownloader()
        self.assertIsNotNone(downloader)

    def test_get_filename_from_url(self):
        """Test extracting filename from URL."""
        from scorefinder.downloader import FileDownloader
        
        downloader = FileDownloader()
        
        url = "https://example.com/path/to/song.musicxml"
        filename = downloader.get_filename_from_url(url)
        
        self.assertEqual(filename, "song.musicxml")


class TestConfig(unittest.TestCase):
    """Test configuration."""

    def test_config_import(self):
        """Test importing config."""
        from scorefinder.config import config
        self.assertIsNotNone(config)

    def test_config_has_attributes(self):
        """Test config has required attributes."""
        from scorefinder.config import config
        
        self.assertTrue(hasattr(config, 'google_api_key'))
        self.assertTrue(hasattr(config, 'google_search_engine_id'))
        self.assertTrue(hasattr(config, 'musescore_path'))
        self.assertTrue(hasattr(config, 'output_dir'))
        self.assertTrue(hasattr(config, 'temp_dir'))


if __name__ == '__main__':
    unittest.main()
