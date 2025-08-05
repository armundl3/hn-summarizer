"""
LLM API-based summarizer using external APIs (OpenAI).
"""

import os
import requests
from typing import List

from .base import BaseSummarizer
from .basic import BasicSummarizer
from ..models import ArticleContent, SummarizerConfig, HNComment, EnhancedSummary
from ..config import (
    OPENAI_API_URL,
    OPENAI_DEFAULT_MODEL,
    OPENAI_MAX_TOKENS,
    OPENAI_ENHANCED_MAX_TOKENS,
    OPENAI_TEMPERATURE,
    OPENAI_TIMEOUT,
    MAX_COMMENTS_FOR_SUMMARY,
    KEY_POINTS_COUNT,
    RELATED_LINKS_COUNT,
)
from ..logging_config import get_logger, log_performance


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
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Initialized LLMAPISummarizer with model: {self.model}, max_tokens: {self.max_tokens}")
    
    def summarize(self, content: ArticleContent) -> List[str]:
        """Generate summary using LLM API with optional fallback to basic."""
        if not content.content:
            return self._format_no_content_summary(content)
        
        try:
            return self._generate_api_summary(content)
        except Exception as e:
            if self.config.allow_fallback:
                print(f"LLM API summarization failed: {e}")
                print("Falling back to basic summarization...")
                return self.fallback.summarize(content)
            else:
                raise RuntimeError(f"LLM API summarization failed: {e}. Use --fallback to enable basic mode fallback.") from e
    
    def enhanced_summarize(self, content: ArticleContent, comments: List[HNComment], story_id: int) -> EnhancedSummary:
        """Generate enhanced summary with article content, comments, and related links."""
        try:
            return self._generate_enhanced_api_summary(content, comments, story_id)
        except Exception as e:
            if self.config.allow_fallback:
                print(f"Enhanced LLM API summarization failed: {e}")
                print("Falling back to basic enhanced summary...")
                return self._generate_basic_enhanced_summary(content, comments, story_id)
            else:
                raise RuntimeError(f"Enhanced LLM API summarization failed: {e}. Use --fallback to enable basic mode fallback.") from e
    
    def _generate_api_summary(self, content: ArticleContent) -> List[str]:
        """Generate summary using OpenAI API."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            if self.config.allow_fallback:
                print("OPENAI_API_KEY not found, falling back to basic mode")
                return self.fallback.summarize(content)
            else:
                raise RuntimeError("OPENAI_API_KEY environment variable not set. Use --fallback to enable basic mode fallback.")
        
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
        
        # If no valid response, handle based on fallback setting
        if self.config.allow_fallback:
            return self.fallback.summarize(content)
        else:
            raise RuntimeError("LLM API returned empty response. Use --fallback to enable basic mode fallback.")
    
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
            self.logger.debug(f"Successfully parsed {len(lines)} lines from LLM API response")
            return lines[:3]
        elif len(lines) > 0:
            self.logger.warning(f"LLM API response only had {len(lines)} lines, padding with default content")
            # Extend with placeholder content if needed
            original_count = len(lines)
            while len(lines) < 3:
                if len(lines) == 1:
                    lines.append("Additional context available in source article.")
                    self.logger.debug("Added default line: 'Additional context available in source article.'")
                else:
                    lines.append("Full details available at source URL.")
                    self.logger.debug("Added default line: 'Full details available at source URL.'")
            self.logger.info(f"Padded LLM API summary from {original_count} to {len(lines)} lines with defaults")
            return lines[:3]
        
        self.logger.error("LLM API response contained no valid lines after parsing")
        return []
    
    def _generate_enhanced_api_summary(self, content: ArticleContent, comments: List[HNComment], story_id: int) -> EnhancedSummary:
        """Generate enhanced summary using OpenAI API."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            if self.config.allow_fallback:
                print("OPENAI_API_KEY not found, falling back to basic mode")
                return self._generate_basic_enhanced_summary(content, comments, story_id)
            else:
                raise RuntimeError("OPENAI_API_KEY environment variable not set. Use --fallback to enable basic mode fallback.")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
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
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": OPENAI_ENHANCED_MAX_TOKENS,
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
            return self._parse_enhanced_summary_response(summary_text, content, story_id)
        
        # If no valid response, handle based on fallback setting
        if self.config.allow_fallback:
            return self._generate_basic_enhanced_summary(content, comments, story_id)
        else:
            raise RuntimeError("LLM API returned empty enhanced response. Use --fallback to enable basic mode fallback.")
    
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
        """Parse the enhanced summary response from API."""
        import re
        
        self.logger.debug(f"Parsing enhanced summary response from LLM API ({len(response_text)} chars)")
        
        # Initialize default values
        article_summary = "Article summary not available."
        comment_summary = "Comment summary not available."
        key_points = ["Key insights not available."] * KEY_POINTS_COUNT
        related_links = ["Related topic research suggested."] * RELATED_LINKS_COUNT
        
        # Track what we're using defaults for
        using_defaults = []
        
        # Parse article summary
        article_match = re.search(r'ARTICLE_SUMMARY:\s*\n(.*?)(?=\n[A-Z_]+:|$)', response_text, re.DOTALL)
        if article_match:
            article_summary = article_match.group(1).strip()
            self.logger.debug("Successfully parsed article summary from LLM API response")
        else:
            using_defaults.append("article_summary")
            self.logger.warning("Failed to parse ARTICLE_SUMMARY from LLM API response, using default")
        
        # Parse comment summary
        comment_match = re.search(r'COMMENT_SUMMARY:\s*\n(.*?)(?=\n[A-Z_]+:|$)', response_text, re.DOTALL)
        if comment_match:
            comment_summary = comment_match.group(1).strip()
            self.logger.debug("Successfully parsed comment summary from LLM API response")
        else:
            using_defaults.append("comment_summary")
            self.logger.warning("Failed to parse COMMENT_SUMMARY from LLM API response, using default")
        
        # Parse key points
        key_points_match = re.search(r'KEY_POINTS:\s*\n(.*?)(?=\n[A-Z_]+:|$)', response_text, re.DOTALL)
        if key_points_match:
            points_text = key_points_match.group(1).strip()
            points = re.findall(r'\d+\.\s*(.*?)(?=\n\d+\.|\n[A-Z_]+:|$)', points_text, re.DOTALL)
            if points:
                key_points = [point.strip() for point in points[:KEY_POINTS_COUNT]]
                self.logger.debug(f"Successfully parsed {len(points)} key points from LLM API response")
                # Pad if fewer points found
                original_count = len(key_points)
                while len(key_points) < KEY_POINTS_COUNT:
                    key_points.append("Additional insights available in full discussion.")
                if len(key_points) > original_count:
                    self.logger.info(f"Padded key points from {original_count} to {KEY_POINTS_COUNT} with defaults")
            else:
                using_defaults.append("key_points")
                self.logger.warning("Found KEY_POINTS section but failed to parse numbered items, using defaults")
        else:
            using_defaults.append("key_points")
            self.logger.warning("Failed to parse KEY_POINTS from LLM API response, using defaults")
        
        # Parse related links
        links_match = re.search(r'RELATED_LINKS:\s*\n(.*?)(?=\n[A-Z_]+:|$)', response_text, re.DOTALL)
        if links_match:
            links_text = links_match.group(1).strip()
            links = re.findall(r'\d+\.\s*(.*?)(?=\n\d+\.|\n[A-Z_]+:|$)', links_text, re.DOTALL)
            if links:
                related_links = [link.strip() for link in links[:RELATED_LINKS_COUNT]]
                self.logger.debug(f"Successfully parsed {len(links)} related links from LLM API response")
                # Pad if fewer links found
                original_count = len(related_links)
                while len(related_links) < RELATED_LINKS_COUNT:
                    related_links.append("Explore related topics in the field.")
                if len(related_links) > original_count:
                    self.logger.info(f"Padded related links from {original_count} to {RELATED_LINKS_COUNT} with defaults")
            else:
                using_defaults.append("related_links")
                self.logger.warning("Found RELATED_LINKS section but failed to parse numbered items, using defaults")
        else:
            using_defaults.append("related_links")
            self.logger.warning("Failed to parse RELATED_LINKS from LLM API response, using defaults")
        
        # Log summary of what defaults were used
        if using_defaults:
            self.logger.warning(f"Enhanced summary using defaults for: {', '.join(using_defaults)}")
            self.logger.debug(f"LLM API response that failed parsing: {response_text[:500]}...")
        else:
            self.logger.info("Successfully parsed all enhanced summary components from LLM API response")
        
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
        self.logger.info("Generating basic enhanced summary fallback (all components will be generic)")
        
        # Create basic article summary using the existing method
        basic_summary = self.fallback.summarize(content)
        article_summary = " ".join(basic_summary[:2]) if len(basic_summary) >= 2 else "Article content summarized."
        self.logger.debug(f"Using basic article summary from {len(basic_summary)} fallback lines")
        
        # Create basic comment summary
        if comments:
            comment_count = len(comments)
            top_commenters = list(set([c.by for c in comments[:5] if c.by]))[:3]
            commenter_text = ", ".join(top_commenters) if top_commenters else "community members"
            comment_summary = f"Discussion with {comment_count} comments from {commenter_text} covering various perspectives on the topic."
            self.logger.debug(f"Generated generic comment summary for {comment_count} comments")
        else:
            comment_summary = "Limited discussion available for this article."
            self.logger.debug("Using default comment summary (no comments available)")
        
        # Generate basic key points
        key_points = [
            "Main article discusses the core topic and its implications",
            "Community discussion provides additional insights and perspectives",
            "Topic represents current trends and developments in the field"
        ]
        self.logger.warning("Using 3 generic default key points (no AI-generated insights)")
        
        # Generate basic related links  
        topic_words = content.title.split()[0:3] if content.title else ["this topic"]
        related_links = [
            f"Search for more information about {' '.join(topic_words)}",
            "Explore related discussions on Hacker News",
            "Research current developments in this technology area"
        ]
        self.logger.warning("Using 3 generic default related links (no AI-generated suggestions)")
        
        return EnhancedSummary(
            article_summary=article_summary,
            comment_summary=comment_summary,
            key_points=key_points,
            related_links=related_links,
            original_url=content.url,
            hn_discussion_url=f"https://news.ycombinator.com/item?id={story_id}"
        )