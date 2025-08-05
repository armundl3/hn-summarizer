# HN Summarizer

A Python tool to fetch and summarize the top articles from Hacker News.

## Features

- Fetches top 20 (or custom number) articles from Hacker News
- Extracts article content from linked URLs
- Generates 3-line summaries for each article using multiple modes:
  - **Basic mode**: Simple text processing (default)
  - **Ollama mode**: Local LLM summarization via Ollama
  - **LLM API mode**: Cloud-based LLM summarization (OpenAI GPT-3.5-turbo)
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

# Use different summarization modes
hn-summarizer --mode basic      # Default text processing
hn-summarizer --mode ollama     # Local LLM via Ollama
hn-summarizer --mode llmapi     # OpenAI GPT-3.5-turbo

# Combine options
hn-summarizer -c 5 -o output.txt -m ollama
```

### Summarization Modes

#### Basic Mode (Default)
Uses simple text processing to extract the first few sentences from articles.

```bash
# These commands are equivalent
hn-summarizer
hn-summarizer --mode basic
hn-summarizer -m basic
```

#### Ollama Mode
Uses a local LLM via [Ollama](https://ollama.ai/) for more intelligent summarization.

**Prerequisites:**
1. Install [Ollama](https://ollama.ai)
2. Pull the required model:
   ```bash
   ollama run qwen3:8b
   ```
   * configure the [OLLAMA_DEFAULT_MODEL](https://github.com/armundl3/hn-summarizer/blob/432c599af03f29611d50fa2704e3bc3cb8d4adab/hn_summarizer/config.py#L35)
3. Ensure Ollama is running (default: `localhost:11434`)

**Usage:**
```bash
# Use Ollama for summarization
hn-summarizer --mode ollama
hn-summarizer -m ollama -c 5

# If Ollama is unavailable, automatically falls back to basic mode
```

#### LLM API Mode
Uses OpenAI's GPT-3.5-turbo for high-quality summarization.

**Prerequisites:**
1. Get an OpenAI API key: https://platform.openai.com/api-keys
2. Set the environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

**Usage:**
```bash
# Use OpenAI API for summarization
hn-summarizer --mode llmapi
hn-summarizer -m llmapi -c 10 -o ai_summaries.txt

# If API key is missing or request fails, automatically falls back to basic mode
```

### Complete Examples

```bash
# Basic usage with simple text processing
hn-summarizer -c 5

# Generate AI-powered summaries with local Ollama
hn-summarizer -c 10 -m ollama -o ollama_summaries.txt

# Use OpenAI for premium summarization
OPENAI_API_KEY="sk-..." hn-summarizer -c 3 -m llmapi

# Combine all options
hn-summarizer --count 15 --mode ollama --output daily_summary.txt
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

- Python 3.10+
- Poetry (for development)

### Optional Requirements by Mode

- **Basic mode**: No additional requirements
- **Ollama mode**: [Ollama](https://ollama.ai/) installed and running locally
- **LLM API mode**: OpenAI API key

## Dependencies

- `requests` - HTTP requests and API calls
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML parser
- `click` - Command-line interface

## Troubleshooting

### Ollama Mode Issues
- **"Connection refused"**: Ensure Ollama is installed and running (`ollama serve`)
- **Model not found**: Pull the required model (`ollama pull llama3.2`)
- **Slow responses**: Large models may take time; consider using smaller models

### LLM API Mode Issues
- **"API key not found"**: Set the `OPENAI_API_KEY` environment variable
- **Rate limits**: OpenAI has usage limits; consider upgrading your plan
- **Network issues**: API calls require internet connectivity

### General Issues
- **No articles found**: Check your internet connection
- **Content extraction fails**: Some websites block automated access
- All modes automatically fall back to basic mode on failure