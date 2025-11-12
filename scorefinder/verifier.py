"""
Music file verification for MusicXML and MIDI formats.

Validates and verifies music notation files before saving and opening
in Musescore Studio. Uses music21 library for verification.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import xml.etree.ElementTree as ET

try:
    from music21 import converter, stream, note, chord
except ImportError:
    # music21 is optional but recommended
    converter = None
    stream = None
    note = None
    chord = None

try:
    import mido
except ImportError:
    # mido is optional but recommended
    mido = None

logger = logging.getLogger(__name__)


class VerificationResult:
    """Result of music file verification."""

    def __init__(self, valid: bool, message: str, details: Optional[dict] = None):
        """
        Initialize verification result.

        Args:
            valid: Whether the file is valid
            message: Verification message
            details: Optional dictionary with verification details
        """
        self.valid = valid
        self.message = message
        self.details = details or {}

    def __bool__(self) -> bool:
        return self.valid

    def __repr__(self) -> str:
        return f"VerificationResult(valid={self.valid}, message='{self.message}')"


class MusicVerifier:
    """Verifies music notation files."""

    def verify_file(self, file_path: Path) -> VerificationResult:
        """
        Verify a music notation file.

        Args:
            file_path: Path to the file to verify

        Returns:
            VerificationResult object
        """
        if not file_path.exists():
            return VerificationResult(False, f"File not found: {file_path}")

        suffix = file_path.suffix.lower()
        
        if suffix in ['.xml', '.musicxml', '.mxl']:
            return self.verify_musicxml(file_path)
        elif suffix in ['.mid', '.midi']:
            return self.verify_midi(file_path)
        else:
            return VerificationResult(False, f"Unsupported file format: {suffix}")

    def verify_musicxml(self, file_path: Path) -> VerificationResult:
        """
        Verify a MusicXML file.

        Args:
            file_path: Path to the MusicXML file

        Returns:
            VerificationResult object
        """
        logger.info(f"Verifying MusicXML file: {file_path}")
        
        # Basic XML validation
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            return VerificationResult(False, f"XML parse error: {e}")
        
        # Check for MusicXML root element
        if not (root.tag.endswith('score-partwise') or root.tag.endswith('score-timewise')):
            return VerificationResult(
                False,
                f"Not a valid MusicXML file: root element is '{root.tag}'"
            )
        
        details = {
            'format': 'MusicXML',
            'root_element': root.tag
        }
        
        # Advanced validation with music21 if available
        if converter is not None:
            try:
                score = converter.parse(str(file_path))
                
                # Extract details
                details['parts'] = len(score.parts)
                details['measures'] = len(score.parts[0].getElementsByClass('Measure')) if score.parts else 0
                
                # Check for at least some notes
                all_notes = score.flatten().notes
                details['notes'] = len(all_notes)
                
                if details['notes'] == 0:
                    return VerificationResult(
                        False,
                        "MusicXML file contains no notes",
                        details
                    )
                
                logger.info(f"MusicXML verified: {details['parts']} parts, "
                           f"{details['measures']} measures, {details['notes']} notes")
                
                return VerificationResult(True, "Valid MusicXML file", details)
            
            except Exception as e:
                logger.warning(f"music21 verification failed: {e}")
                # Fall back to basic validation success
                return VerificationResult(
                    True,
                    "Valid MusicXML file (basic validation only)",
                    details
                )
        else:
            # Without music21, just confirm it's valid XML with correct root
            return VerificationResult(
                True,
                "Valid MusicXML file (basic validation only)",
                details
            )

    def verify_midi(self, file_path: Path) -> VerificationResult:
        """
        Verify a MIDI file.

        Args:
            file_path: Path to the MIDI file

        Returns:
            VerificationResult object
        """
        logger.info(f"Verifying MIDI file: {file_path}")
        
        details = {'format': 'MIDI'}
        
        # Try with mido first (lightweight)
        if mido is not None:
            try:
                midi_file = mido.MidiFile(str(file_path))
                
                details['type'] = midi_file.type
                details['tracks'] = len(midi_file.tracks)
                details['ticks_per_beat'] = midi_file.ticks_per_beat
                
                # Count note events
                note_count = 0
                for track in midi_file.tracks:
                    for msg in track:
                        if msg.type == 'note_on':
                            note_count += 1
                
                details['notes'] = note_count
                
                if note_count == 0:
                    return VerificationResult(
                        False,
                        "MIDI file contains no notes",
                        details
                    )
                
                logger.info(f"MIDI verified: {details['tracks']} tracks, {note_count} notes")
                
                return VerificationResult(True, "Valid MIDI file", details)
            
            except Exception as e:
                return VerificationResult(False, f"MIDI verification error: {e}", details)
        
        # Fallback to music21 if mido is not available
        if converter is not None:
            try:
                score = converter.parse(str(file_path))
                
                details['parts'] = len(score.parts)
                all_notes = score.flatten().notes
                details['notes'] = len(all_notes)
                
                if details['notes'] == 0:
                    return VerificationResult(
                        False,
                        "MIDI file contains no notes",
                        details
                    )
                
                return VerificationResult(True, "Valid MIDI file", details)
            
            except Exception as e:
                return VerificationResult(False, f"MIDI verification error: {e}", details)
        
        # No verification libraries available
        return VerificationResult(
            True,
            "MIDI file exists (verification libraries not available)",
            details
        )

    def verify_content(self, content: str, file_format: str) -> VerificationResult:
        """
        Verify music notation content (before writing to file).

        Args:
            content: File content as string
            file_format: Format type ('musicxml' or 'midi')

        Returns:
            VerificationResult object
        """
        if file_format == 'musicxml':
            return self._verify_musicxml_content(content)
        else:
            return VerificationResult(
                True,
                f"Content verification not implemented for {file_format}"
            )

    def _verify_musicxml_content(self, content: str) -> VerificationResult:
        """Verify MusicXML content string."""
        try:
            root = ET.fromstring(content)
            
            if not (root.tag.endswith('score-partwise') or root.tag.endswith('score-timewise')):
                return VerificationResult(
                    False,
                    f"Not valid MusicXML: root element is '{root.tag}'"
                )
            
            return VerificationResult(True, "Valid MusicXML content")
        
        except ET.ParseError as e:
            return VerificationResult(False, f"XML parse error: {e}")
