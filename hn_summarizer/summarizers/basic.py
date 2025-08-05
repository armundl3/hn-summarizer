"""
Basic text processing summarizer.
"""

import re
from typing import List

from .base import BaseSummarizer
from ..models import ArticleContent
from ..config import MIN_SENTENCE_LENGTH, MAX_LINE_LENGTH


class BasicSummarizer(BaseSummarizer):
    """Basic summarizer using simple text processing."""
    
    def summarize(self, content: ArticleContent) -> List[str]:
        """Generate a basic summary using text processing."""
        if not content.content:
            self.logger.debug("No content available, using no-content fallback")
            return self._format_no_content_summary(content)
        
        # Extract sentences
        sentences = self._extract_sentences(content.content)
        self.logger.debug(f"Extracted {len(sentences)} sentences from {len(content.content)} chars of content")
        
        # Create summary lines
        summary_lines = self._create_summary_lines(content.title, sentences, content.url)
        
        return self._ensure_line_count(summary_lines, content)
    
    def _extract_sentences(self, content: str) -> List[str]:
        """Extract and filter sentences from content."""
        sentences = re.split(r'[.!?]+', content)
        sentences = [
            s.strip() for s in sentences 
            if len(s.strip()) > MIN_SENTENCE_LENGTH
        ]
        return sentences
    
    def _create_summary_lines(self, title: str, sentences: List[str], url: str) -> List[str]:
        """Create summary lines from title and sentences."""
        summary_lines = [f"Article: {title}"]
        defaults_used = []
        
        # First content line
        if sentences:
            first_sentence = sentences[0]
            if len(first_sentence) > MAX_LINE_LENGTH:
                first_sentence = first_sentence[:MAX_LINE_LENGTH] + "..."
                self.logger.debug(f"Truncated first sentence to {MAX_LINE_LENGTH} chars")
            summary_lines.append(first_sentence)
        else:
            default_line = "No content available."
            summary_lines.append(default_line)
            defaults_used.append(f"first content line: '{default_line}'")
        
        # Second content line
        if len(sentences) > 1:
            second_sentence = sentences[1]
            if len(second_sentence) > MAX_LINE_LENGTH:
                second_sentence = second_sentence[:MAX_LINE_LENGTH] + "..."
                self.logger.debug(f"Truncated second sentence to {MAX_LINE_LENGTH} chars")
            summary_lines.append(second_sentence)
        else:
            default_line = f"URL: {url}"
            summary_lines.append(default_line)
            defaults_used.append(f"second content line: '{default_line}'")
        
        if defaults_used:
            self.logger.warning(f"BasicSummarizer using defaults for: {'; '.join(defaults_used)}")
        
        return summary_lines