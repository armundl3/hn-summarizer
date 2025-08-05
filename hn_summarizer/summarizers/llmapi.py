"""
LLM API-based summarizer using external APIs (OpenAI).
"""

import os
import requests
from typing import List

from .base import BaseSummarizer
from .basic import BasicSummarizer
from ..models import ArticleContent, SummarizerConfig
from ..config import (
    OPENAI_API_URL,
    OPENAI_DEFAULT_MODEL,
    OPENAI_MAX_TOKENS,
    OPENAI_TEMPERATURE,
    OPENAI_TIMEOUT,
)


class LLMAPISummarizer(BaseSummarizer):
    """Summarizer using external LLM APIs (OpenAI)."""
    
    def __init__(self, config: SummarizerConfig):
        super().__init__(config)
        self.api_url = OPENAI_API_URL
        self.model = config.model_name or OPENAI_DEFAULT_MODEL
        self.max_tokens = config.max_tokens or OPENAI_MAX_TOKENS
        self.temperature = config.temperature or OPENAI_TEMPERATURE
        self.timeout = config.timeout or OPENAI_TIMEOUT
        self.fallback = BasicSummarizer(config)
    
    def summarize(self, content: ArticleContent) -> List[str]:
        """Generate summary using LLM API with fallback to basic."""
        if not content.content:
            return self._format_no_content_summary(content)
        
        try:
            return self._generate_api_summary(content)
        except Exception as e:
            print(f"LLM API summarization failed: {e}")
            print("Falling back to basic summarization...")
            return self.fallback.summarize(content)
    
    def _generate_api_summary(self, content: ArticleContent) -> List[str]:
        """Generate summary using OpenAI API."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OPENAI_API_KEY not found, falling back to basic mode")
            return self.fallback.summarize(content)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = self._create_prompt(content.title, content.content)
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        summary_text = result["choices"][0]["message"]["content"].strip()
        
        if summary_text:
            lines = self._parse_summary_response(summary_text)
            return self._ensure_line_count(lines, content)
        
        # If no valid response, use fallback
        return self.fallback.summarize(content)
    
    def _create_prompt(self, title: str, content: str) -> str:
        """Create prompt for API summarization."""
        return f"""Summarize the following article in exactly 3 lines:

Title: {title}
Content: {content[:2000]}

Please provide exactly 3 concise lines that capture the key points."""
    
    def _parse_summary_response(self, response_text: str) -> List[str]:
        """Parse and clean the summary response from API."""
        lines = response_text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        # Ensure we have valid lines
        if len(lines) >= 3:
            return lines[:3]
        elif len(lines) > 0:
            # Extend with placeholder content if needed
            while len(lines) < 3:
                if len(lines) == 1:
                    lines.append("Additional context available in source article.")
                else:
                    lines.append("Full details available at source URL.")
            return lines[:3]
        
        return []