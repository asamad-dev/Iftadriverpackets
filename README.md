# 🚛 Driver Packet Processing System

A simple tool that reads driver trip sheets using AI and extracts the data automatically.

## What it does
- Takes photos of handwritten driver trip sheets
- Uses AI to read and extract trip information
- Saves results to spreadsheet files
- Works with both web interface and command line

## Quick Start

### 1. Install Python packages
```bash
pip install -r requirements.txt
```

### 2. Get your API key
1. Go to https://makersuite.google.com/
2. Create a free account
3. Generate an API key

### 3. Set up your API key
Create a file called `.env` in this folder and add:
```
GEMINI_API_KEY=your_api_key_here
```

### 4. Run the app
**Web Interface (Recommended):**
```bash
streamlit run streamlit_app.py
```
Then open your browser to http://localhost:8501

**Command Line:**
```bash
python src/gemini_example.py
```

## How to use

### Web Interface
1. Drag and drop your driver packet images
2. Click "Process Images"
3. Download the results as CSV or JSON

### Command Line
1. Put your images in the `input/` folder
2. Run the program
3. Choose option 1 to process all images
4. Results saved in `output/` folder

## What you get
- **CSV file**: Easy to open in Excel with all trip data
- **JSON file**: Detailed results with validation info
- **Automatic corrections**: Fixes common OCR errors

## Common Issues
- **"API key not found"**: Make sure your `.env` file has the correct API key
- **"Import error"**: Run `pip install -r requirements.txt` again
- **"Port already in use"**: Try `streamlit run streamlit_app.py --server.port 8502`

## File Structure
```
├── streamlit_app.py          # Web interface
├── src/gemini_example.py     # Command line interface
├── input/                    # Put your images here
├── output/                   # Results saved here
└── .env                      # Your API key (create this)
```

## Features
- ✅ Reads handwritten text accurately
- ✅ Extracts dates, locations, driver info, trailer numbers
- ✅ Fixes common mistakes automatically
- ✅ Works with multiple images at once
- ✅ Easy-to-use web interface
- ✅ Exports to Excel-compatible formats

Need help? Check that your API key is correct and your images are clear and readable.
