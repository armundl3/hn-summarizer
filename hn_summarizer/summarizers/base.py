"""
Base class for article summarizers.
"""

from abc import ABC, abstractmethod
from typing import List

from ..models import ArticleContent, SummarizerConfig
from ..config import SUMMARY_LINES
from ..logging_config import get_logger


class BaseSummarizer(ABC):
    """Abstract base class for article summarizers."""
    
    def __init__(self, config: SummarizerConfig):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
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
        original_count = len(lines)
        
        # Truncate if too many lines
        if len(lines) > SUMMARY_LINES:
            self.logger.debug(f"Truncating summary from {len(lines)} to {SUMMARY_LINES} lines")
            return lines[:SUMMARY_LINES]
        
        # Pad if too few lines
        defaults_added = []
        while len(lines) < SUMMARY_LINES:
            if len(lines) == 0:
                line = f"Article: {content.title}"
                lines.append(line)
                defaults_added.append(f"title fallback: '{line}'")
            elif len(lines) == 1:
                line = "Content not available for detailed summarization."
                lines.append(line)
                defaults_added.append(f"content fallback: '{line}'")
            else:
                line = f"URL: {content.url}"
                lines.append(line)
                defaults_added.append(f"URL fallback: '{line}'")
        
        if defaults_added:
            self.logger.warning(f"Padded summary from {original_count} to {SUMMARY_LINES} lines with defaults: {'; '.join(defaults_added)}")
        
        return lines[:SUMMARY_LINES]
    
    def _format_no_content_summary(self, content: ArticleContent) -> List[str]:
        """
        Generate a fallback summary when content is not available.
        
        Args:
            content: The article content (with empty content)
            
        Returns:
            List of fallback summary lines
        """
        self.logger.warning(f"Using no-content fallback summary for '{content.title}' (reason: {content.error_message or 'empty content'})")
        
        url_display = content.url
        if len(url_display) > 80:
            url_display = url_display[:80] + "..."
        
        fallback_lines = [
            f"Title: {content.title}",
            "Content not available for summarization.",
            f"URL: {url_display}" if url_display else "No URL available"
        ]
        
        self.logger.debug(f"Generated no-content fallback: {fallback_lines}")
        return fallback_lines