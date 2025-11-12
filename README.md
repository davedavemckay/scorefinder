# ScoreFinder

A Python application that leverages Google Gemini and Google Search to find digital notation of drum music. ScoreFinder can search for music in MusicXML, MIDI, or other formats, convert them as needed, verify the files, and launch them in Musescore Studio for editing.

## Features

- 🔍 **Smart Search**: Uses Google Custom Search API to find drum notation files
- 🤖 **AI-Powered Conversion**: Converts various formats to MusicXML using Google Gemini
- ✅ **Format Verification**: Validates MusicXML and MIDI files before saving
- 🎵 **Musescore Integration**: Automatically opens verified files in Musescore Studio
- 📦 **Multiple Format Support**: Handles MusicXML, MIDI, ABC, Guitar Pro, PDF, and more

## Installation

### Prerequisites

- Python 3.8 or higher
- Google API Key (for Gemini AI)
- Google Custom Search Engine ID
- Musescore Studio (optional, for opening files)

### Install from source

```bash
git clone https://github.com/davedavemckay/scorefinder.git
cd scorefinder
pip install -r requirements.txt
pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API credentials:
```env
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
MUSESCORE_PATH=/path/to/musescore
```

### Getting API Credentials

#### Google API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

#### Google Custom Search Engine ID
1. Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Create a new search engine
3. Enable "Search the entire web"
4. Copy the Search Engine ID to your `.env` file

## Usage

### Check Configuration

```bash
scorefinder check
```

This will verify your API keys, Musescore installation, and dependencies.

### Find and Open Drum Notation

```bash
scorefinder find "Seven Nation Army" --artist "The White Stripes"
```

This command will:
1. Search Google for drum notation files
2. Download or fetch the content
3. Convert to MusicXML if needed (using Gemini AI)
4. Verify the file format
5. Save to the `scores` directory
6. Open in Musescore Studio

### Search Only (No Download)

```bash
scorefinder search "Enter Sandman" --artist "Metallica"
```

Lists search results without downloading or converting.

## How It Works

### 1. Search Phase
- Uses Google Custom Search API to find drum notation files
- Looks for MusicXML, MIDI, PDF, ABC, and other music formats
- Ranks results by relevance

### 2. Processing Phase
- **MusicXML/MIDI files**: Downloads directly and verifies
- **Other formats**: Downloads content and converts using Google Gemini AI

### 3. Verification Phase
- Validates XML structure for MusicXML files
- Checks for required elements (notes, measures, parts)
- Uses music21 library for advanced verification (if installed)
- Uses mido library for MIDI verification (if installed)

### 4. Launch Phase
- Saves verified files to the output directory
- Opens files in Musescore Studio for editing
- Platform-specific launching (Windows, macOS, Linux)

## Project Structure

```
scorefinder/
├── scorefinder/          # Main package
│   ├── __init__.py      # Package initialization
│   ├── app.py           # Main application logic
│   ├── cli.py           # Command-line interface
│   ├── config.py        # Configuration management
│   ├── search.py        # Google Search integration
│   ├── converter.py     # Gemini AI format conversion
│   ├── verifier.py      # File verification
│   ├── launcher.py      # Musescore launcher
│   └── downloader.py    # File download utility
├── main.py              # Entry point script
├── setup.py             # Package setup
├── requirements.txt     # Dependencies
├── .env.example         # Example configuration
└── README.md           # This file
```

## Dependencies

### Core Dependencies
- `google-generativeai`: Google Gemini AI API
- `google-api-python-client`: Google Search API
- `python-dotenv`: Environment variable management
- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `click`: CLI framework
- `colorama`: Terminal colors

### Optional Dependencies (Recommended)
- `music21`: Advanced music notation processing and verification
- `mido`: MIDI file handling and verification

## Verification Details

ScoreFinder uses parts of the verification approach from the [MuseScore project](https://github.com/musescore/musescore) to ensure files are valid:

- **XML Structure**: Validates proper XML syntax and structure
- **MusicXML Schema**: Checks for required elements (score-partwise, parts, measures)
- **Content Validation**: Ensures files contain actual musical content (notes, rhythms)
- **Format Compliance**: Verifies MIDI files have valid headers and tracks

## Examples

### Find drum notation for a specific song
```bash
scorefinder find "Tom Sawyer" --artist "Rush"
```

### Search without opening in Musescore
```bash
scorefinder find "YYZ" --artist "Rush" --no-open
```

### Check if everything is configured correctly
```bash
scorefinder check
```

## Troubleshooting

### "Google API key is required"
Make sure you've created a `.env` file with your `GOOGLE_API_KEY`.

### "Musescore not found"
Install Musescore Studio or set the correct path in `.env`:
- Windows: `C:\Program Files\MuseScore 4\bin\MuseScore4.exe`
- macOS: `/Applications/MuseScore 4.app/Contents/MacOS/mscore`
- Linux: `/usr/bin/mscore`

### Advanced verification disabled
Install optional dependencies for better verification:
```bash
pip install music21 mido
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Uses [Google Gemini](https://ai.google.dev/) for AI-powered format conversion
- Uses [Google Custom Search](https://developers.google.com/custom-search) for finding notation files
- Verification approach inspired by [MuseScore](https://github.com/musescore/musescore)
- Music processing powered by [music21](http://web.mit.edu/music21/)
