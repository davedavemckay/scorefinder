# Quick Start Guide

Get started with ScoreFinder in 5 minutes!

## 1. Installation

```bash
# Clone the repository
git clone https://github.com/davedavemckay/scorefinder.git
cd scorefinder

# Run the installation script (Linux/macOS)
./install.sh

# Or install manually:
pip install -r requirements.txt
pip install -e .
```

## 2. Configuration

Create a `.env` file from the template:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
GOOGLE_API_KEY=your_actual_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

### Getting API Keys

**Google API Key (Gemini):**
1. Visit https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key to your `.env` file

**Google Custom Search Engine ID:**
1. Visit https://programmablesearchengine.google.com/
2. Click "Add" to create a new search engine
3. Set "Search the entire web" to ON
4. Copy the "Search engine ID" to your `.env` file

## 3. Verify Setup

```bash
python main.py check
```

You should see all green checkmarks (✓). If Musescore is not found, install it or set the path in `.env`.

## 4. Find Your First Score

```bash
python main.py find "Seven Nation Army" --artist "The White Stripes"
```

This will:
- 🔍 Search for drum notation
- 📥 Download the file
- 🔄 Convert if needed
- ✅ Verify the file
- 💾 Save to `scores/`
- 🎵 Open in Musescore Studio

## 5. Explore Features

### Search without downloading:
```bash
python main.py search "Enter Sandman" --artist "Metallica"
```

### Find and save without opening:
```bash
python main.py find "Tom Sawyer" --artist "Rush" --no-open
```

### Get help:
```bash
python main.py --help
python main.py find --help
```

## Troubleshooting

### "Google API key is required"
- Make sure you created a `.env` file
- Verify your API keys are correct
- Check there are no extra spaces or quotes

### "Musescore not found"
- Install Musescore Studio from https://musescore.org/
- Or set `MUSESCORE_PATH` in `.env` to the correct location

### "No results found"
- Try with different search terms
- Add or remove the artist name
- Check your internet connection
- Verify your Google Search Engine ID is correct

## Next Steps

- Read the full [README.md](README.md) for detailed information
- Check [USAGE.md](USAGE.md) for more examples
- See [DEVELOPMENT.md](DEVELOPMENT.md) for technical details

## Common Commands

```bash
# Check configuration
python main.py check

# Find and open a score
python main.py find "Song Name" --artist "Artist Name"

# Search only (no download)
python main.py search "Song Name"

# Find without opening in Musescore
python main.py find "Song Name" --no-open

# Get version
python main.py --version

# Get help
python main.py --help
```

## Example Workflow

1. **Search first** to see what's available:
   ```bash
   python main.py search "Master of Puppets" --artist "Metallica"
   ```

2. **Find and download** the best result:
   ```bash
   python main.py find "Master of Puppets" --artist "Metallica"
   ```

3. **Edit in Musescore** (opens automatically)

4. **Check your scores** directory:
   ```bash
   ls scores/
   ```

That's it! You're ready to find and edit drum notation with ScoreFinder. 🎵
