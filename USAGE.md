# ScoreFinder Usage Examples

## Basic Usage

### 1. Configuration Check
Before using ScoreFinder, check your configuration:
```bash
python main.py check
```

Expected output when properly configured:
```
╔══════════════════════════════════════════════╗
║         ScoreFinder Configuration           ║
╚══════════════════════════════════════════════╝

API Configuration:
  ✓ Google API Key: Set
  ✓ Google Search Engine ID: Set

Musescore Studio:
  Path: /usr/bin/mscore
  Status: Available

Directories:
  Output: scores
  Temp: temp

Optional Dependencies:
  ✓ music21: Installed
  ✓ mido: Installed

──────────────────────────────────────────────
✓ Configuration is complete
```

### 2. Search for Drum Notation
Search for drum notation without downloading:
```bash
python main.py search "Enter Sandman" --artist "Metallica"
```

This will list available results with their formats and URLs.

### 3. Find and Open Drum Notation
Find drum notation and automatically open in Musescore:
```bash
python main.py find "Seven Nation Army" --artist "The White Stripes"
```

Process:
1. 🔍 Searches Google for drum notation files
2. 📥 Downloads or fetches the file
3. 🔄 Converts to MusicXML if needed (using Gemini AI)
4. ✅ Verifies the file format and content
5. 💾 Saves to the `scores` directory
6. 🎵 Opens in Musescore Studio

### 4. Find Without Auto-Opening
If you want to review the file before opening in Musescore:
```bash
python main.py find "Tom Sawyer" --artist "Rush" --no-open
```

## Advanced Examples

### Example 1: Popular Rock Song
```bash
python main.py find "Smells Like Teen Spirit" --artist "Nirvana"
```

### Example 2: Jazz Standard
```bash
python main.py find "Take Five" --artist "Dave Brubeck"
```

### Example 3: Metal Song
```bash
python main.py find "Master of Puppets" --artist "Metallica"
```

### Example 4: Classic Rock
```bash
python main.py find "Moby Dick" --artist "Led Zeppelin"
```

## Understanding the Output

### Successful Search
```
🔍 Searching for drum notation...
✓ Found 10 results

📄 Result 1/10: Seven Nation Army - Drum Score
   Format: musicxml
   URL: https://example.com/scores/seven-nation-army.xml
   Downloading musicxml file...
   ✓ Downloaded
   Verifying...
   ✓ Verified: Valid MusicXML file
      format: MusicXML
      parts: 1
      measures: 48
      notes: 384

✓ Successfully saved to: scores/Seven_Nation_Army.musicxml

🎵 Opening in Musescore Studio...
✓ Musescore launched successfully

✓ Success!
```

### Conversion Example
When a non-MusicXML format is found:
```
📄 Result 1/10: Tom Sawyer - Drum Tab (PDF)
   Format: pdf
   URL: https://example.com/tabs/tom-sawyer.pdf
   Converting pdf to MusicXML...
   ✓ Converted to MusicXML
   Verifying...
   ✓ Verified
```

### No Results Found
```
🔍 Searching for drum notation...
❌ No results found

✗ Failed to find or process notation
```

## Workflow Tips

### 1. Start with a Search
Before downloading, search to see what's available:
```bash
python main.py search "Song Name" --artist "Artist Name"
```

### 2. Review Multiple Results
The application tries multiple search results automatically if the first one fails.

### 3. Check Your Output Directory
All downloaded files are saved to the `scores` directory. Review them:
```bash
ls -lh scores/
```

### 4. Manual Verification
Even though files are automatically verified, you can inspect them:
```bash
cat scores/Song_Name.musicxml
```

## Troubleshooting Examples

### Error: "Google API key is required"
Create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Error: "Musescore not found"
Set the correct path in `.env`:
```env
# For Linux
MUSESCORE_PATH=/usr/bin/mscore

# For Windows
MUSESCORE_PATH=C:\Program Files\MuseScore 4\bin\MuseScore4.exe

# For macOS
MUSESCORE_PATH=/Applications/MuseScore 4.app/Contents/MacOS/mscore
```

### Warning: "Advanced verification disabled"
Install optional dependencies:
```bash
pip install music21 mido
```

## File Formats Supported

### Direct Support (No Conversion)
- **MusicXML** (.xml, .musicxml, .mxl) - Preferred format
- **MIDI** (.mid, .midi) - Direct support

### Conversion Supported (via Gemini AI)
- **PDF** - Text extraction + AI conversion
- **ABC Notation** - Text-based notation
- **Guitar Pro** - If text representation available
- **Other text formats** - Various notation formats

## API Usage Considerations

### Google Search API
- Has usage limits (100 queries per day on free tier)
- Consider the query cost when searching

### Google Gemini API
- Has usage limits based on your plan
- Conversion of complex formats may require multiple API calls

### Recommendation
Use the `search` command first to verify results exist before using `find` to save API calls.
