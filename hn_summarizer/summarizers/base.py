"""
Base class for article summarizers.
"""

from abc import ABC, abstractmethod
from typing import List

from ..models import ArticleContent, SummarizerConfig
from ..config import SUMMARY_LINES


class BaseSummarizer(ABC):
    """Abstract base class for article summarizers."""
    
    def __init__(self, config: SummarizerConfig):
        self.config = config
    
    @abstractmethod
    def summarize(self, content: ArticleContent) -> List[str]:
        """
        Generate a summary for the given article content.
        
        Args:
            content: The article content to summarize
            
        Returns:
            List of summary lines (typically 3 lines)
        """
        pass
    
    def _ensure_line_count(self, lines: List[str], content: ArticleContent) -> List[str]:
        """
        Ensure we have exactly the required number of summary lines.
        
        Args:
            lines: Generated summary lines
            content: Original content for fallback info
            
        Returns:
            List with exactly SUMMARY_LINES lines
        """
        # Remove empty lines
        lines = [line.strip() for line in lines if line.strip()]
        
        # Truncate if too many lines
        if len(lines) > SUMMARY_LINES:
            return lines[:SUMMARY_LINES]
        
        # Pad if too few lines
        while len(lines) < SUMMARY_LINES:
            if len(lines) == 0:
                lines.append(f"Article: {content.title}")
            elif len(lines) == 1:
                lines.append("Content not available for detailed summarization.")
            else:
                lines.append(f"URL: {content.url}")
        
        return lines[:SUMMARY_LINES]
    
    def _format_no_content_summary(self, content: ArticleContent) -> List[str]:
        """
        Generate a fallback summary when content is not available.
        
        Args:
            content: The article content (with empty content)
            
        Returns:
            List of fallback summary lines
        """
        url_display = content.url
        if len(url_display) > 80:
            url_display = url_display[:80] + "..."
        
        return [
            f"Title: {content.title}",
            "Content not available for summarization.",
            f"URL: {url_display}" if url_display else "No URL available"
        ]