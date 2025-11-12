"""
Google Gemini integration for format conversion.

Uses Google Gemini AI to convert various music notation formats
to MusicXML format.
"""

import logging
from typing import Optional
import google.generativeai as genai

from .config import config

logger = logging.getLogger(__name__)


class FormatConverter:
    """Converts music notation formats using Google Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the format converter.

        Args:
            api_key: Google API key (uses config if not provided)
        """
        self.api_key = api_key or config.google_api_key
        if not self.api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def convert_to_musicxml(self, content: str, source_format: str) -> str:
        """
        Convert music notation from another format to MusicXML.

        Args:
            content: The content to convert (text-based format)
            source_format: The source format (e.g., 'abc', 'pdf-text', 'guitar-pro-text')

        Returns:
            MusicXML content as a string

        Raises:
            Exception: If conversion fails
        """
        logger.info(f"Converting from {source_format} to MusicXML")
        
        prompt = self._build_conversion_prompt(content, source_format)
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract MusicXML from response
            musicxml = self._extract_musicxml(response.text)
            
            logger.info("Conversion successful")
            return musicxml
        
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise

    def _build_conversion_prompt(self, content: str, source_format: str) -> str:
        """Build the prompt for Gemini to convert the notation."""
        prompt = f"""You are a music notation expert. Convert the following {source_format} drum notation to MusicXML format.

The drum notation should be converted accurately, preserving:
- Time signatures
- Note values and rhythms
- Drum instrument mappings (snare, bass drum, hi-hat, cymbals, toms, etc.)
- Dynamics and articulations
- Measure structure

Input format: {source_format}
Input content:
{content}

Please provide ONLY the valid MusicXML output, starting with <?xml version="1.0"?> and containing the complete <score-partwise> structure.
Ensure the MusicXML is valid and can be parsed by standard music notation software.
"""
        return prompt

    def _extract_musicxml(self, response_text: str) -> str:
        """Extract MusicXML content from Gemini's response."""
        # Remove markdown code blocks if present
        text = response_text.strip()
        
        if '```xml' in text:
            # Extract from code block
            start = text.find('```xml') + 6
            end = text.find('```', start)
            text = text[start:end].strip()
        elif '```' in text:
            # Generic code block
            start = text.find('```') + 3
            end = text.find('```', start)
            text = text[start:end].strip()
        
        # Ensure it starts with XML declaration
        if not text.startswith('<?xml'):
            # Try to find the start of XML
            xml_start = text.find('<?xml')
            if xml_start != -1:
                text = text[xml_start:]
            else:
                # Add XML declaration if missing
                text = '<?xml version="1.0" encoding="UTF-8"?>\n' + text
        
        return text

    def enhance_drum_notation(self, musicxml_content: str) -> str:
        """
        Use Gemini to enhance or fix drum notation in MusicXML.

        Args:
            musicxml_content: Existing MusicXML content

        Returns:
            Enhanced MusicXML content
        """
        logger.info("Enhancing drum notation with Gemini")
        
        prompt = f"""You are a music notation expert. Review and enhance the following MusicXML drum notation.

Tasks:
1. Verify the drum notation is correct and complete
2. Ensure proper drum instrument mappings
3. Fix any structural issues
4. Add missing metadata if appropriate

MusicXML content:
{musicxml_content}

Please provide the corrected and enhanced MusicXML output. Provide ONLY the valid MusicXML, no explanations.
"""
        
        try:
            response = self.model.generate_content(prompt)
            enhanced_xml = self._extract_musicxml(response.text)
            logger.info("Enhancement successful")
            return enhanced_xml
        
        except Exception as e:
            logger.error(f"Enhancement failed: {e}")
            # Return original if enhancement fails
            return musicxml_content
