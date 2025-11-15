"""
Google Gemini integration for format conversion.

Uses Google Gemini AI to convert various music notation formats
to MusicXML format.
"""

import logging
from pathlib import Path
from typing import Optional
import io

import google.generativeai as genai
from PyPDF2 import PdfReader
from pdf2image import convert_from_path

from .config import config

logger = logging.getLogger(__name__)

# Configure the generative AI model
genai.configure(api_key=config.gemini_api_key)
# Use the stable model name for gemini-1.5-flash
model = genai.GenerativeModel('gemini-1.5-flash')

# Define a token limit, leaving a buffer for the prompt and other overhead
TOKEN_LIMIT = 1000000 

class FormatConverter:
    """Converts different music notation formats to MusicXML."""

    def convert_to_musicxml(self, file_path: Path, source_format: str) -> Optional[str]:
        """
        Convert a file to MusicXML format using Gemini.

        Args:
            file_path: Path to the source file.
            source_format: The format of the source file.

        Returns:
            The content of the converted MusicXML file, or None if conversion fails.
        """
        logger.info(f"Converting {file_path} from {source_format} to MusicXML...")

        try:
            if source_format == 'pdf':
                return self._convert_pdf_in_chunks(file_path)
            else:
                return self._convert_binary_in_chunks(file_path, source_format)

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            print(f"   ❌ Conversion failed: {e}")
            return None

    def _convert_pdf_in_chunks(self, file_path: Path) -> Optional[str]:
        """Convert a PDF to MusicXML by processing it page by page as images."""
        try:
            images = convert_from_path(file_path)
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            print(f"   ❌ Failed to convert PDF to images: {e}")
            return None

        full_musicxml = ""
        
        for i, image in enumerate(images):
            print(f"      - Converting page {i + 1}/{len(images)}...")

            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()

            prompt = f"This is an image of a page from a drum score. Convert the musical notation in this image to MusicXML format. Only output the raw XML content."
            
            image_part = {
                "mime_type": "image/png",
                "data": img_bytes
            }

            response = model.generate_content([prompt, image_part])
            full_musicxml += response.text.strip().replace("`", "") + "\n"

        # A post-processing step to merge the XML snippets would be needed here
        # For now, we return the concatenated parts.
        return self._clean_xml_output(full_musicxml)

    def _convert_binary_in_chunks(self, file_path: Path, source_format: str) -> Optional[str]:
        """Convert a binary file (like Guitar Pro) in chunks."""
        content = file_path.read_bytes()
        content_size = len(content)
        chunk_size = TOKEN_LIMIT  # Approximate chunk size in bytes
        full_musicxml = ""

        for i in range(0, content_size, chunk_size):
            chunk = content[i:i + chunk_size]
            part_num = (i // chunk_size) + 1
            total_parts = (content_size + chunk_size - 1) // chunk_size
            
            print(f"      - Converting chunk {part_num}/{total_parts}...")

            prompt = f"This is part {part_num} of {total_parts} of a {source_format} file. Convert this chunk to MusicXML. Only output valid MusicXML."
            
            response = model.generate_content([prompt, chunk])
            full_musicxml += response.text.strip().replace("`", "") + "\n"
        
        return self._clean_xml_output(full_musicxml)

    def _clean_xml_output(self, xml_string: str) -> str:
        """Removes markdown formatting from the LLM's XML output."""
        if xml_string.strip().startswith("xml"):
            xml_string = f"<{xml_string}"
        if "```" in xml_string:
            parts = xml_string.split("```")
            if len(parts) > 1:
                return parts[1].strip().lstrip("xml")
        return xml_string
