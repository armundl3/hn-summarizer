# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
```bash
# Install dependencies
poetry install

# Run with default settings (top 20 articles, basic mode)
poetry run hn-summarizer

# Run with options
poetry run hn-summarizer --count 10 --mode ollama --output summary.txt
poetry run hn-summarizer -c 5 -m llmapi -o output.txt

# Use custom Ollama model (only applies to ollama mode)
poetry run hn-summarizer --mode ollama --ollama-model llama3.2:7b
poetry run hn-summarizer -m ollama --ollama-model mistral:7b -c 5

# Error handling and fallback behavior (default: no fallback)
poetry run hn-summarizer --mode ollama  # Will fail with error if Ollama unavailable
poetry run hn-summarizer --mode ollama --fallback  # Will fallback to basic mode if Ollama fails
poetry run hn-summarizer -m llmapi --fallback -c 3  # Will fallback to basic if no API key

# Logging and debugging
poetry run hn-summarizer --log-level DEBUG  # Detailed debug logging
poetry run hn-summarizer --log-level INFO   # Default info logging  
poetry run hn-summarizer --log-file app.log  # Log to file instead of stderr
poetry run hn-summarizer --log-level DEBUG --log-file debug.log -c 2  # Debug 2 articles to file
```

### Development Commands
```bash
# Install development dependencies
poetry install --group dev

# Run tests
poetry run pytest

# Run tests with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_cli.py

# Format code
poetry run black .

# Lint code  
poetry run flake8

# Type checking
poetry run mypy hn_summarizer
```

### Testing Individual Components
```bash
# Test specific functionality
poetry run pytest tests/test_fetchers.py::TestHackerNewsAPI
poetry run pytest tests/test_summarizers.py -k "test_basic"
```

## Architecture Overview

### Core Components

**Main Entry Point**: `hn_summarizer/cli.py` - Click-based CLI interface with options for count, output file, and summarization mode.

**Orchestrator**: `hn_summarizer/summarizer.py` - `HackerNewsSummarizer` class coordinates the entire process:
- Fetches story IDs from HN API
- Extracts article content from URLs  
- Generates summaries using pluggable summarizers
- Handles enhanced mode with comments for ollama/llmapi modes

**Data Layer**: `hn_summarizer/fetchers.py` contains:
- `HackerNewsAPI` - Fetches stories and comments from HN Firebase API
- `ContentExtractor` - Scrapes article content from URLs using BeautifulSoup

**Summarization Strategy Pattern**: `hn_summarizer/summarizers/` directory implements three modes:
- `BasicSummarizer` - Simple text processing (extracts first few sentences)
- `OllamaSummarizer` - Local LLM via Ollama API with enhanced analysis
- `LLMAPISummarizer` - OpenAI GPT-3.5-turbo with enhanced analysis

**Models**: `hn_summarizer/models.py` defines dataclasses for HNStory, ArticleContent, HNComment, EnhancedSummary, etc.

**Configuration**: `hn_summarizer/config.py` centralizes all constants including API endpoints, timeouts, content selectors, and model settings.

### Key Architectural Patterns

**Strategy Pattern**: Summarizers implement `BaseSummarizer` abstract class, allowing runtime mode switching.

**Enhanced Mode**: Ollama and LLM API modes fetch comments alongside articles to provide richer summaries with key insights and related links.

**Error-First Design**: By default, ollama and llmapi modes fail with clear error messages if external services are unavailable. Use `--fallback` flag to enable automatic fallback to basic mode.

**Rate Limiting**: Built-in delays between requests to respect HN API and target websites.

**Comprehensive Logging**: Full performance and debugging logs available at multiple levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) with timing metrics for all operations.

### Summarization Modes

- **Basic**: Extracts first meaningful sentences from article content
- **Ollama**: Uses local mistral:7b model (configurable) for AI summarization with comment analysis  
- **LLM API**: Uses OpenAI GPT-3.5-turbo for premium summarization with comment analysis

Enhanced modes (ollama/llmapi) generate `EnhancedSummary` objects with article summary, comment summary, key points, and related exploration links.

### External Dependencies

- **Ollama**: Requires local Ollama installation and model (default: mistral:7b)
- **OpenAI**: Requires OPENAI_API_KEY environment variable
- **Web Scraping**: Uses requests + BeautifulSoup with configurable content selectors for different website layouts

### Logging and Performance

The application includes comprehensive logging at multiple checkpoints:

- **Performance Timing**: All major operations (API calls, content extraction, summarization) are timed
- **Request Tracking**: Every HN API call and web request is logged with URLs and response details
- **Error Handling**: All failures include detailed error messages with context
- **Processing Metrics**: Success/failure counts and processing times for each article
- **Debug Information**: Content lengths, model choices, fallback usage, and response parsing
- **Default Content Detection**: Detailed logging when summarizers use default/fallback content instead of AI-generated summaries

Use `--log-level DEBUG` to see detailed execution flow and `--log-file path.log` to capture logs to a file for analysis.

### Debugging Default Content Usage

The application now logs exactly when and why default content is used instead of AI-generated summaries:

- **WARNING**: `"Enhanced summary using defaults for: article_summary, key_points"` - Shows which enhanced components failed to parse
- **WARNING**: `"Using 3 generic default key points (no AI-generated insights)"` - Basic fallback summaries 
- **WARNING**: `"Padded summary from 1 to 3 lines with defaults"` - When AI response is too short
- **DEBUG**: Shows actual response content that failed parsing for troubleshooting

This is extremely helpful for debugging why summarization quality might be poor - check logs for default usage patterns.