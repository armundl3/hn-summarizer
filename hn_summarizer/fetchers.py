"""
Content fetching functionality for HN Summarizer.
"""

import re
import requests
from typing import List, Optional
from bs4 import BeautifulSoup

from .config import (
    HN_API_BASE_URL,
    HN_TOP_STORIES_ENDPOINT, 
    HN_ITEM_ENDPOINT,
    DEFAULT_USER_AGENT,
    REQUEST_TIMEOUT,
    MAX_CONTENT_LENGTH,
    CONTENT_SELECTORS,
)
from .models import HNStory, ArticleContent, HNComment


class HackerNewsAPI:
    """Client for interacting with the Hacker News API."""
    
    def __init__(self):
        self.base_url = HN_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
    
    def get_top_story_ids(self, limit: int = 20) -> List[int]:
        """Fetch top story IDs from Hacker News API."""
        try:
            url = f"{self.base_url}{HN_TOP_STORIES_ENDPOINT}"
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            story_ids = response.json()[:limit]
            return story_ids
        except requests.RequestException as e:
            print(f"Error fetching top stories: {e}")
            return []
    
    def get_story_details(self, story_id: int) -> Optional[HNStory]:
        """Fetch details for a specific story."""
        try:
            url = f"{self.base_url}{HN_ITEM_ENDPOINT.format(story_id)}"
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                return None
                
            return HNStory(
                id=data.get("id", story_id),
                title=data.get("title", "No title"),
                url=data.get("url"),
                score=data.get("score", 0),
                by=data.get("by"),
                time=data.get("time"),
                descendants=data.get("descendants"),
                type=data.get("type", "story")
            )
        except requests.RequestException as e:
            print(f"Error fetching story {story_id}: {e}")
            return None
    
    def get_comment(self, comment_id: int) -> Optional[HNComment]:
        """Fetch details for a specific comment."""
        try:
            url = f"{self.base_url}{HN_ITEM_ENDPOINT.format(comment_id)}"
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if not data or data.get("type") != "comment":
                return None
                
            return HNComment(
                id=data.get("id", comment_id),
                text=data.get("text", ""),
                by=data.get("by"),
                time=data.get("time"),
                parent=data.get("parent"),
                kids=data.get("kids", [])
            )
        except requests.RequestException as e:
            print(f"Error fetching comment {comment_id}: {e}")
            return None
    
    def get_top_comments(self, story: HNStory, max_comments: int = 20) -> List[HNComment]:
        """Fetch top-level comments for a story."""
        comments = []
        
        if not story.descendants or not hasattr(story, 'kids'):
            # Need to fetch story details to get comment IDs
            story_details = self.get_story_details(story.id)
            if not story_details or 'kids' not in story_details.__dict__:
                return comments
            comment_ids = getattr(story_details, 'kids', [])
        else:
            comment_ids = getattr(story, 'kids', [])
        
        # Fetch comments up to max_comments limit
        for comment_id in comment_ids[:max_comments]:
            comment = self.get_comment(comment_id)
            if comment and comment.text.strip():  # Only include non-empty comments
                comments.append(comment)
                
        return comments
    
    def get_story_with_comments(self, story_id: int, max_comments: int = 20) -> Optional[tuple]:
        """Fetch story with its top comments."""
        try:
            # Get story details first
            url = f"{self.base_url}{HN_ITEM_ENDPOINT.format(story_id)}"
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                return None
                
            story = HNStory(
                id=data.get("id", story_id),
                title=data.get("title", "No title"),
                url=data.get("url"),
                score=data.get("score", 0),
                by=data.get("by"),
                time=data.get("time"),
                descendants=data.get("descendants"),
                type=data.get("type", "story")
            )
            
            # Fetch comments
            comments = []
            comment_ids = data.get("kids", [])
            
            for comment_id in comment_ids[:max_comments]:
                comment = self.get_comment(comment_id)
                if comment and comment.text.strip():
                    comments.append(comment)
            
            return story, comments
            
        except requests.RequestException as e:
            print(f"Error fetching story with comments {story_id}: {e}")
            return None


class ContentExtractor:
    """Extracts article content from web pages."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
    
    def extract_content(self, story: HNStory) -> ArticleContent:
        """Extract article content from a story's URL."""
        if not story.url:
            return ArticleContent(
                title=story.title,
                content="",
                url="",
                extracted_successfully=False,
                error_message="No URL available"
            )
        
        try:
            response = self.session.get(story.url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Remove script and style elements
            for element in soup(["script", "style"]):
                element.extract()
            
            # Try to find main content using selectors
            content = self._extract_main_content(soup)
            
            # Fallback to body if no main content found
            if not content:
                content = self._extract_body_content(soup)
            
            # Clean up text
            content = self._clean_content(content)
            
            return ArticleContent(
                title=story.title,
                content=content,
                url=story.url,
                extracted_successfully=True
            )
            
        except Exception as e:
            return ArticleContent(
                title=story.title,
                content="",
                url=story.url or "",
                extracted_successfully=False,
                error_message=str(e)
            )
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Try to extract main content using content selectors."""
        for selector in CONTENT_SELECTORS:
            elements = soup.select(selector)
            if elements:
                return elements[0].get_text()
        return ""
    
    def _extract_body_content(self, soup: BeautifulSoup) -> str:
        """Fallback to extracting content from body."""
        if soup.body:
            return soup.body.get_text()
        return soup.get_text()
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize extracted content."""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        # Limit content length
        return content[:MAX_CONTENT_LENGTH]