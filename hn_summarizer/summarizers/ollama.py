"""
Ollama-based summarizer using local LLM.
"""

import requests
from typing import List

from .base import BaseSummarizer
from .basic import BasicSummarizer
from ..models import ArticleContent, SummarizerConfig
from ..config import (
    OLLAMA_BASE_URL,
    OLLAMA_GENERATE_ENDPOINT,
    OLLAMA_DEFAULT_MODEL,
    OLLAMA_TIMEOUT,
)


class OllamaSummarizer(BaseSummarizer):
    """Summarizer using Ollama local LLM."""
    
    def __init__(self, config: SummarizerConfig):
        super().__init__(config)
        self.base_url = OLLAMA_BASE_URL
        self.model = config.model_name or OLLAMA_DEFAULT_MODEL
        self.timeout = config.timeout or OLLAMA_TIMEOUT
        self.fallback = BasicSummarizer(config)
    
    def summarize(self, content: ArticleContent) -> List[str]:
        """Generate summary using Ollama LLM with fallback to basic."""
        if not content.content:
            return self._format_no_content_summary(content)
        
        try:
            return self._generate_ollama_summary(content)
        except Exception as e:
            print(f"Ollama summarization failed: {e}")
            print("Falling back to basic summarization...")
            return self.fallback.summarize(content)
    
    def _generate_ollama_summary(self, content: ArticleContent) -> List[str]:
        """Generate summary using Ollama API."""
        url = f"{self.base_url}{OLLAMA_GENERATE_ENDPOINT}"
        
        prompt = self._create_prompt(content.title, content.content)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature or 0.7,
                "max_tokens": self.config.max_tokens or 200
            }
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        
        result = response.json()
        summary_text = result.get("response", "").strip()
        
        if summary_text:
            lines = self._parse_summary_response(summary_text)
            return self._ensure_line_count(lines, content)
        
        # If no valid response, use fallback
        return self.fallback.summarize(content)
    
    def _create_prompt(self, title: str, content: str) -> str:
        """Create prompt for Ollama summarization."""
        return f"""Summarize the following article in exactly 3 lines:

Title: {title}
Content: {content[:2000]}

Provide a concise 3-line summary:"""
    
    def _parse_summary_response(self, response_text: str) -> List[str]:
        """Parse and clean the summary response from Ollama."""
        lines = response_text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        # Ensure we have valid lines
        if len(lines) >= 3:
            return lines[:3]
        elif len(lines) > 0:
            # Extend with placeholder content if needed
            while len(lines) < 3:
                if len(lines) == 1:
                    lines.append("Additional details available in full article.")
                else:
                    lines.append("See source for more information.")
            return lines[:3]
        
        return []