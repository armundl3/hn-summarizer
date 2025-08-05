"""
Data models and type definitions for HN Summarizer.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class SummarizerMode(Enum):
    """Available summarization modes."""
    BASIC = "basic"
    OLLAMA = "ollama"
    LLMAPI = "llmapi"


@dataclass
class HNStory:
    """Represents a Hacker News story."""
    id: int
    title: str
    url: Optional[str] = None
    score: int = 0
    by: Optional[str] = None
    time: Optional[int] = None
    descendants: Optional[int] = None
    type: str = "story"


@dataclass 
class ArticleContent:
    """Represents extracted article content."""
    title: str
    content: str
    url: str
    extracted_successfully: bool = True
    error_message: Optional[str] = None


@dataclass
class ArticleSummary:
    """Represents a summarized article."""
    story: HNStory
    content: ArticleContent
    summary_lines: List[str]
    mode_used: SummarizerMode
    processing_time: Optional[float] = None
    fallback_used: bool = False


@dataclass
class SummarizerConfig:
    """Configuration for a summarizer."""
    mode: SummarizerMode
    timeout: int = 30
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model_name: Optional[str] = None