# HN Summarizer

A Python tool to fetch and summarize the top articles from Hacker News.

## Features

- Fetches top 20 (or custom number) articles from Hacker News
- Extracts article content from linked URLs
- Generates 3-line summaries for each article
- Command-line interface with customizable options
- Built with Poetry for easy dependency management

## Installation

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone <repo-url>
cd hn-summarizer

# Install dependencies
poetry install

# Run the tool
poetry run hn-summarizer
```

### Using pip

```bash
# Install from source
pip install .

# Run the tool
hn-summarizer
```

## Usage

### Basic usage
```bash
# Summarize top 20 articles
poetry run hn-summarizer

# Or if installed globally
hn-summarizer
```

### Options
```bash
# Summarize top 10 articles
hn-summarizer --count 10

# Save output to file
hn-summarizer --output summaries.txt

# Combine options
hn-summarizer -c 5 -o output.txt
```

## Development

### Setup
```bash
# Install development dependencies
poetry install --group dev

# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run flake8

# Type checking
poetry run mypy hn_summarizer
```

## Project Structure

```
hn-summarizer/
├── hn_summarizer/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   └── summarizer.py   # Core functionality
├── tests/
├── pyproject.toml      # Poetry configuration
└── README.md
```

## Requirements

- Python 3.8+
- Poetry (for development)

## Dependencies

- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML parser
- `click` - Command-line interface