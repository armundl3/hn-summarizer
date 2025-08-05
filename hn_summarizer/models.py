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
class HNComment:
    """Represents a Hacker News comment."""
    id: int
    text: str
    by: Optional[str] = None
    time: Optional[int] = None
    parent: Optional[int] = None
    kids: Optional[List[int]] = None


@dataclass
class EnhancedSummary:
    """Enhanced summary with article content, comments, and related links."""
    article_summary: str
    comment_summary: str
    key_points: List[str]
    related_links: List[str]
    original_url: str
    hn_discussion_url: str


@dataclass
class ArticleSummary:
    """Represents a summarized article."""
    story: HNStory
    content: ArticleContent
    summary_lines: List[str]
    mode_used: SummarizerMode
    enhanced_summary: Optional[EnhancedSummary] = None
    processing_time: Optional[float] = None
    fallback_used: bool = False


@dataclass
class SummarizerConfig:
    """Configuration for a summarizer."""
    mode: SummarizerMode
    timeout: int = 60
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model_name: Optional[str] = None
    ollama_model: Optional[str] = None
    allow_fallback: bool = True