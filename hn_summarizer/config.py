"""
Configuration constants and settings for HN Summarizer.
"""

# Hacker News API settings
HN_API_BASE_URL = "https://hacker-news.firebaseio.com/v0"
HN_TOP_STORIES_ENDPOINT = "/topstories.json"
HN_ITEM_ENDPOINT = "/item/{}.json"

# HTTP settings
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)
REQUEST_TIMEOUT = 10
RATE_LIMIT_DELAY = 1  # seconds between requests

# Content extraction settings
MAX_CONTENT_LENGTH = 5000
MIN_SENTENCE_LENGTH = 20

# Summarization settings
SUMMARY_LINES = 3
MAX_LINE_LENGTH = 120

# Enhanced summarization settings
MAX_COMMENTS_TO_FETCH = 15
MAX_COMMENTS_FOR_SUMMARY = 10
ENHANCED_SUMMARY_TOKENS = 800
KEY_POINTS_COUNT = 3
RELATED_LINKS_COUNT = 3

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_GENERATE_ENDPOINT = "/api/generate"
OLLAMA_DEFAULT_MODEL = "mistral:7b"
OLLAMA_TIMEOUT = 30

# OpenAI API settings
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_DEFAULT_MODEL = "gpt-3.5-turbo"
OPENAI_MAX_TOKENS = 200
OPENAI_ENHANCED_MAX_TOKENS = 1000
OPENAI_TEMPERATURE = 0.7
OPENAI_TIMEOUT = 30

# Content selectors for article extraction
CONTENT_SELECTORS = [
    "article",
    '[role="main"]',
    ".content",
    ".post-content",
    ".entry-content",
    ".article-content",
    "main",
    ".story-body",
]