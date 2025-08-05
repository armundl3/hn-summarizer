"""
Hacker News Article Summarizer
A Python tool to fetch and summarize top Hacker News articles
"""

from .summarizer import HackerNewsSummarizer
from .models import SummarizerMode, HNStory, ArticleContent, ArticleSummary
from .fetchers import HackerNewsAPI, ContentExtractor
from .summarizers import BaseSummarizer, BasicSummarizer, OllamaSummarizer, LLMAPISummarizer

__version__ = "0.1.0"

__all__ = [
    "HackerNewsSummarizer",
    "SummarizerMode",
    "HNStory", 
    "ArticleContent",
    "ArticleSummary",
    "HackerNewsAPI",
    "ContentExtractor",
    "BaseSummarizer",
    "BasicSummarizer",
    "OllamaSummarizer", 
    "LLMAPISummarizer",
]
