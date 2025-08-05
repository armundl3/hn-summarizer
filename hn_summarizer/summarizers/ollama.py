"""
Ollama-based summarizer using local LLM.
"""

import requests
from typing import List

from .base import BaseSummarizer
from .basic import BasicSummarizer
from ..models import ArticleContent, SummarizerConfig, HNComment, EnhancedSummary
from ..config import (
    OLLAMA_BASE_URL,
    OLLAMA_GENERATE_ENDPOINT,
    OLLAMA_DEFAULT_MODEL,
    OLLAMA_TIMEOUT,
    MAX_COMMENTS_FOR_SUMMARY,
    ENHANCED_SUMMARY_TOKENS,
    KEY_POINTS_COUNT,
    RELATED_LINKS_COUNT,
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
    
    def enhanced_summarize(self, content: ArticleContent, comments: List[HNComment], story_id: int) -> EnhancedSummary:
        """Generate enhanced summary with article content, comments, and related links."""
        try:
            return self._generate_enhanced_ollama_summary(content, comments, story_id)
        except Exception as e:
            print(f"Enhanced Ollama summarization failed: {e}")
            print("Falling back to basic enhanced summary...")
            return self._generate_basic_enhanced_summary(content, comments, story_id)
    
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
    
    def _generate_enhanced_ollama_summary(self, content: ArticleContent, comments: List[HNComment], story_id: int) -> EnhancedSummary:
        """Generate enhanced summary using Ollama API."""
        url = f"{self.base_url}{OLLAMA_GENERATE_ENDPOINT}"
        
        # Prepare comment text
        comment_texts = []
        for comment in comments[:MAX_COMMENTS_FOR_SUMMARY]:
            if comment.text.strip():
                # Remove HTML tags from comment text
                import re
                clean_text = re.sub(r'<[^>]+>', '', comment.text)
                comment_texts.append(f"Comment by {comment.by or 'Anonymous'}: {clean_text[:500]}")
        
        comments_section = "\n\n".join(comment_texts) if comment_texts else "No significant comments available."
        
        prompt = self._create_enhanced_prompt(content.title, content.content, comments_section)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature or 0.7,
                "max_tokens": ENHANCED_SUMMARY_TOKENS
            }
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        
        result = response.json()
        summary_text = result.get("response", "").strip()
        
        if summary_text:
            return self._parse_enhanced_summary_response(summary_text, content, story_id)
        
        # If no valid response, use fallback
        return self._generate_basic_enhanced_summary(content, comments, story_id)
    
    def _create_enhanced_prompt(self, title: str, content: str, comments: str) -> str:
        """Create enhanced prompt for comprehensive summarization."""
        return f"""Analyze this Hacker News article and discussion comprehensively:

ARTICLE:
Title: {title}
Content: {content[:3000]}

DISCUSSION COMMENTS:
{comments}

Please provide a structured analysis in the following format:

ARTICLE_SUMMARY:
[2-3 sentences summarizing the main article content and key insights]

COMMENT_SUMMARY:
[2-3 sentences summarizing the key points and perspectives from the discussion]

KEY_POINTS:
1. [First key takeaway from article and discussion]
2. [Second key takeaway from article and discussion]  
3. [Third key takeaway from article and discussion]

RELATED_LINKS:
1. [Suggest a relevant search term or topic to explore this subject deeper]
2. [Suggest another relevant search term or related technology/concept]
3. [Suggest a third area for deeper exploration related to this topic]

Provide concrete, specific insights rather than generic summaries."""
    
    def _parse_enhanced_summary_response(self, response_text: str, content: ArticleContent, story_id: int) -> EnhancedSummary:
        """Parse the enhanced summary response from Ollama."""
        import re
        
        # Initialize default values
        article_summary = "Article summary not available."
        comment_summary = "Comment summary not available."
        key_points = ["Key insights not available."] * KEY_POINTS_COUNT
        related_links = ["Related topic research suggested."] * RELATED_LINKS_COUNT
        
        # Parse article summary
        article_match = re.search(r'ARTICLE_SUMMARY:\s*\n(.*?)(?=\n[A-Z_]+:|$)', response_text, re.DOTALL)
        if article_match:
            article_summary = article_match.group(1).strip()
        
        # Parse comment summary
        comment_match = re.search(r'COMMENT_SUMMARY:\s*\n(.*?)(?=\n[A-Z_]+:|$)', response_text, re.DOTALL)
        if comment_match:
            comment_summary = comment_match.group(1).strip()
        
        # Parse key points
        key_points_match = re.search(r'KEY_POINTS:\s*\n(.*?)(?=\n[A-Z_]+:|$)', response_text, re.DOTALL)
        if key_points_match:
            points_text = key_points_match.group(1).strip()
            points = re.findall(r'\d+\.\s*(.*?)(?=\n\d+\.|\n[A-Z_]+:|$)', points_text, re.DOTALL)
            if points:
                key_points = [point.strip() for point in points[:KEY_POINTS_COUNT]]
                # Pad if fewer points found
                while len(key_points) < KEY_POINTS_COUNT:
                    key_points.append("Additional insights available in full discussion.")
        
        # Parse related links
        links_match = re.search(r'RELATED_LINKS:\s*\n(.*?)(?=\n[A-Z_]+:|$)', response_text, re.DOTALL)
        if links_match:
            links_text = links_match.group(1).strip()
            links = re.findall(r'\d+\.\s*(.*?)(?=\n\d+\.|\n[A-Z_]+:|$)', links_text, re.DOTALL)
            if links:
                related_links = [link.strip() for link in links[:RELATED_LINKS_COUNT]]
                # Pad if fewer links found
                while len(related_links) < RELATED_LINKS_COUNT:
                    related_links.append("Explore related topics in the field.")
        
        return EnhancedSummary(
            article_summary=article_summary,
            comment_summary=comment_summary,
            key_points=key_points,
            related_links=related_links,
            original_url=content.url,
            hn_discussion_url=f"https://news.ycombinator.com/item?id={story_id}"
        )
    
    def _generate_basic_enhanced_summary(self, content: ArticleContent, comments: List[HNComment], story_id: int) -> EnhancedSummary:
        """Generate basic fallback enhanced summary."""
        # Create basic article summary using the existing method
        basic_summary = self.fallback.summarize(content)
        article_summary = " ".join(basic_summary[:2]) if len(basic_summary) >= 2 else "Article content summarized."
        
        # Create basic comment summary
        if comments:
            comment_count = len(comments)
            top_commenters = list(set([c.by for c in comments[:5] if c.by]))[:3]
            commenter_text = ", ".join(top_commenters) if top_commenters else "community members"
            comment_summary = f"Discussion with {comment_count} comments from {commenter_text} covering various perspectives on the topic."
        else:
            comment_summary = "Limited discussion available for this article."
        
        # Generate basic key points
        key_points = [
            "Main article discusses the core topic and its implications",
            "Community discussion provides additional insights and perspectives", 
            "Topic represents current trends and developments in the field"
        ]
        
        # Generate basic related links
        related_links = [
            f"Search for more information about {content.title.split()[0:3]}",
            "Explore related discussions on Hacker News",
            "Research current developments in this technology area"
        ]
        
        return EnhancedSummary(
            article_summary=article_summary,
            comment_summary=comment_summary,
            key_points=key_points,
            related_links=related_links,
            original_url=content.url,
            hn_discussion_url=f"https://news.ycombinator.com/item?id={story_id}"
        )