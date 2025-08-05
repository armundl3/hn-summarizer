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
            return self._format_no_content_summary(content)
        
        # Extract sentences
        sentences = self._extract_sentences(content.content)
        
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
        
        # First content line
        if sentences:
            first_sentence = sentences[0]
            if len(first_sentence) > MAX_LINE_LENGTH:
                first_sentence = first_sentence[:MAX_LINE_LENGTH] + "..."
            summary_lines.append(first_sentence)
        else:
            summary_lines.append("No content available.")
        
        # Second content line
        if len(sentences) > 1:
            second_sentence = sentences[1]
            if len(second_sentence) > MAX_LINE_LENGTH:
                second_sentence = second_sentence[:MAX_LINE_LENGTH] + "..."
            summary_lines.append(second_sentence)
        else:
            summary_lines.append(f"URL: {url}")
        
        return summary_lines