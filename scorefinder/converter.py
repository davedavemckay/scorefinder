"""
Google Gemini integration for format conversion.

Uses Google Gemini AI to convert various music notation formats
to MusicXML format.
"""

import logging
from pathlib import Path
from typing import Optional
import io
import random
import os
import shutil
import subprocess
import sys

import google.generativeai as genai
from PyPDF2 import PdfReader, errors
from pdf2image import convert_from_path

from .config import config

logger = logging.getLogger(__name__)

# Configure the generative AI model
genai.configure(api_key=config.gemini_api_key)
model = genai.GenerativeModel(config.llm_model)

# Define a token limit, leaving a buffer for the prompt and other overhead
TOKEN_LIMIT = 1000000 
# Increase the limit to allow for larger songbooks
MAX_PDF_PAGES = 200
MAX_SONG_LENGTH_PAGES = 15 # Max pages for a single song extraction
TOC_SEARCH_THRESHOLD = 10 # Min pages to trigger a TOC search

class FormatConverter:
    """Converts different music notation formats to MusicXML."""

    def convert_to_musicxml(self, file_path: Path, source_format: str, song_name: str, start_page: int = 0) -> Optional[str]:
        """
        Convert a file to MusicXML format using Gemini.
        Now accepts song_name and start_page to aid in searching within documents.

        Args:
            file_path: Path to the source file.
            source_format: The format of the source file.

        Returns:
            The content of the converted MusicXML file, or None if conversion fails.
        """
        logger.info(f"Converting {file_path} from {source_format} to MusicXML...")

        try:
            if source_format == 'pdf':
                return self._convert_pdf_intelligently(file_path, song_name, start_page=start_page)
            else:
                return self._convert_binary_in_chunks(file_path, source_format)

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            print(f"   ❌ Conversion failed: {e}")
            return None

    def _find_song_start_page(self, reader: PdfReader, song_name: str) -> Optional[int]:
        """Tries to find the starting page of a song in a PDF."""
        # Method 1: Check bookmarks (outlines)
        try:
            for dest in reader.outline:
                if isinstance(dest, list): # Handle nested bookmarks
                    continue
                if song_name.lower() in dest.title.lower():
                    page_num = reader.get_destination_page_number(dest)
                    logger.info(f"Found '{song_name}' in bookmarks, starting at page {page_num + 1}.")
                    return page_num
        except Exception:
            logger.warning("Could not parse PDF bookmarks.")

        # Method 2: Scan text of first few pages for a text-based Table of Contents
        logger.info("Searching first 10 pages for a text-based Table of Contents...")
        for i in range(min(10, len(reader.pages))):
            page_text = reader.pages[i].extract_text()
            for line in page_text.split('\n'):
                if song_name.lower() in line.lower():
                    # Find a page number in the same line
                    numbers = [int(s) for s in line.split() if s.isdigit()]
                    if numbers:
                        # Assuming the last number on the line is the page number
                        page_num = numbers[-1] - 1 # Adjust for 0-indexing
                        logger.info(f"Found '{song_name}' in text index, starting at page {page_num + 1}.")
                        return page_num
        
        logger.warning(f"Could not find '{song_name}' in the PDF's index or bookmarks.")
        return None


    def get_pdf_preview_image(self, file_path: Path, song_name: str) -> Optional[tuple[Path, int]]:
        """
        Finds the start page of a song, saves a preview image, and returns the path and page number.
        """
        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)

            if num_pages > MAX_PDF_PAGES:
                print(f"   ⚠️  Skipping: PDF has {num_pages} pages, exceeding the limit of {MAX_PDF_PAGES}.")
                return None, None
            if num_pages == 0:
                print("   ⚠️  Skipping: PDF is empty.")
                return None, None

            start_page = 0
            if num_pages > TOC_SEARCH_THRESHOLD:
                print("      - Searching PDF index for song...")
                found_page = self._find_song_start_page(reader, song_name)
                if found_page is None:
                    print(f"   ⚠️  Skipping: Could not find '{song_name}' in the index of the {num_pages}-page PDF.")
                    return None, None # Could not find the song in the index
                start_page = found_page
            else:
                # For shorter documents, just do a quick content check
                print("      - Verifying PDF content...")
                if not self._pdf_contains_sheet_music(file_path, num_pages):
                    message = "PDF does not appear to contain sheet music."
                    logger.warning(message)
                    print(f"   ⚠️  Skipping: {message}")
                    return None, None
                print("      ✓ Content looks like sheet music.")
            
            # Create a preview image of the found page
            preview_image = convert_from_path(file_path, first_page=start_page + 1, last_page=start_page + 1)[0]
            preview_image_path = config.temp_dir / f"preview_{file_path.stem}.png"
            preview_image.save(preview_image_path)
            
            return preview_image_path, start_page

        except Exception as e:
            logger.error(f"Failed to generate PDF preview: {e}")
            return None, None

    def _convert_pdf_intelligently(self, file_path: Path, song_name: str, start_page: int = 0) -> Optional[str]:
        """
        Intelligently finds and extracts a single song from a potentially large PDF.
        """
        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)

            if num_pages > MAX_PDF_PAGES:
                print(f"   ⚠️  Skipping: PDF has {num_pages} pages, exceeding the limit of {MAX_PDF_PAGES}.")
                return None
            
            # This method is now called *after* a start page has been confirmed.
            # The TOC search logic is now in get_pdf_preview_image.

            full_musicxml = ""
            # Use the provided start_page; limit extraction to MAX_SONG_LENGTH_PAGES
            last_page_to_convert = min(start_page + MAX_SONG_LENGTH_PAGES, num_pages)
            images = convert_from_path(file_path, first_page=start_page + 1, last_page=last_page_to_convert)
            
            # Extract page by page from the starting point
            for i, image in enumerate(images):
                current_page_num = start_page + i + 1
                print(f"      - Converting page {current_page_num}/{num_pages}...")
                
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                image_part = {"mime_type": "image/png", "data": img_bytes}

                # Prompt to convert and check for continuation
                prompt = "Convert the musical notation in this image to MusicXML. After the XML, on a new line, answer with only 'CONTINUES' if the piece seems to continue, or 'ENDS' if it seems complete."
                
                # Add stream=False to prevent hanging on long generation tasks
                response = model.generate_content([prompt, image_part], stream=False)
                
                content_parts = response.text.rsplit('\n', 1)
                xml_part = content_parts[0]
                status = content_parts[1] if len(content_parts) > 1 else ""

                full_musicxml += self._clean_xml_output(xml_part) + "\n"

                if 'ENDS' in status:
                    print("      ✓ Song appears to be complete.")
                    break
            
            return self._clean_xml_output(full_musicxml)

        except errors.PdfReadError as e:
            logger.error(f"Failed to read PDF: {e}")
            print(f"   ❌ Failed to read PDF, it may be corrupted or not a valid PDF.")
            return None
        except Exception as e:
            logger.error(f"Intelligent PDF conversion failed: {e}")
            print(f"   ❌ PDF processing failed: {e}")
            return None

    def _convert_pdf_in_chunks(self, file_path: Path) -> Optional[str]:
        """
        (DEPRECATED) Convert a PDF to MusicXML by processing it page by page as images,
        with checks for page count and content.
        """
        try:
            # 1. Check page count
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            if num_pages > MAX_PDF_PAGES:
                message = f"PDF has {num_pages} pages, exceeding the limit of {MAX_PDF_PAGES}."
                logger.warning(message)
                print(f"   ⚠️  Skipping: {message}")
                return None
            if num_pages == 0:
                logger.warning("PDF is empty.")
                print("   ⚠️  Skipping: PDF is empty.")
                return None

            # 2. Check a random page for sheet music content
            print("      - Verifying PDF content...")
            if not self._pdf_contains_sheet_music(file_path, num_pages):
                message = "PDF does not appear to contain sheet music."
                logger.warning(message)
                print(f"   ⚠️  Skipping: {message}")
                return None
            print("      ✓ Content looks like sheet music.")

            # If checks pass, proceed with full conversion
            images = convert_from_path(file_path)
        except errors.PdfReadError as e:
            logger.error(f"Failed to read PDF: {e}")
            print(f"   ❌ Failed to read PDF, it may be corrupted or not a valid PDF.")
            return None
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

    def _pdf_contains_sheet_music(self, file_path: Path, num_pages: int) -> bool:
        """Check a random page of a PDF to see if it contains sheet music."""
        # Pick a page from the middle to avoid title pages
        if num_pages > 3:
            page_to_check = random.randint(1, num_pages - 2)
        else:
            page_to_check = 0
        
        try:
            # Convert just one page to an image
            image = convert_from_path(file_path, first_page=page_to_check + 1, last_page=page_to_check + 1)[0]
            
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()

            prompt = "Does this image contain musical sheet music? Answer with only 'yes' or 'no'."
            image_part = {"mime_type": "image/png", "data": img_bytes}
            
            response = model.generate_content([prompt, image_part])
            
            return 'yes' in response.text.lower()
        except Exception as e:
            logger.error(f"Could not verify PDF content: {e}")
            # Default to assuming it's valid to avoid false negatives
            return True

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
