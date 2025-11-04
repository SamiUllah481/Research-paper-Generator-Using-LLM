# AI Research Paper Generator

This project uses Google's Generative AI (Gemini) to create comprehensive research papers on any topic. It automatically performs web research using DuckDuckGo and Wikipedia, then generates a well-structured academic paper with proper citations.

## Features

- Automatic web research using DuckDuckGo and Wikipedia
- Academic paper generation with Google Gemini AI
- PDF output with Unicode support
- Proper citations and references
- Command-line interface with customizable options

## Requirements

- Python 3.8+
- Google GenAI API key
- Required packages (see `Requirements.txt`)

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r Requirements.txt
```
4. Create a `.env` file with your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

Basic usage:
```bash
python main_simple.py --query "Your research topic" --out output_file.pdf
```

Options:
- `--query` or `-q`: Research topic or question
- `--model` or `-m`: GenAI model to use (default: gemini-2.5-flash)
- `--out` or `-o`: Output filename (PDF)