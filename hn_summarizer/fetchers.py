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
from .logging_config import get_logger, log_performance


class HackerNewsAPI:
    """Client for interacting with the Hacker News API."""
    
    def __init__(self):
        self.base_url = HN_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
        self.logger = get_logger(self.__class__.__name__)
        self.logger.debug(f"Initialized HackerNewsAPI with base URL: {self.base_url}")
    
    @log_performance(get_logger("HackerNewsAPI.get_top_story_ids"), "fetching top story IDs")
    def get_top_story_ids(self, limit: int = 20) -> List[int]:
        """Fetch top story IDs from Hacker News API."""
        url = f"{self.base_url}{HN_TOP_STORIES_ENDPOINT}"
        self.logger.debug(f"Fetching top story IDs from: {url}")
        
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            all_story_ids = response.json()
            story_ids = all_story_ids[:limit]
            
            self.logger.info(f"Successfully fetched {len(story_ids)} story IDs (out of {len(all_story_ids)} available)")
            self.logger.debug(f"Story IDs: {story_ids[:5]}{'...' if len(story_ids) > 5 else ''}")
            return story_ids
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch top stories from {url}: {e}")
            return []
    
    def get_story_details(self, story_id: int) -> Optional[HNStory]:
        """Fetch details for a specific story."""
        url = f"{self.base_url}{HN_ITEM_ENDPOINT.format(story_id)}"
        self.logger.debug(f"Fetching story details for {story_id} from: {url}")
        
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                self.logger.warning(f"Empty response for story {story_id}")
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
            
            self.logger.debug(f"Successfully fetched story {story_id}: '{story.title[:50]}...', score: {story.score}")
            return story
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch story {story_id}: {e}")
            return None
    
    def get_comment(self, comment_id: int) -> Optional[HNComment]:
        """Fetch details for a specific comment."""
        url = f"{self.base_url}{HN_ITEM_ENDPOINT.format(comment_id)}"
        self.logger.debug(f"Fetching comment {comment_id} from: {url}")
        
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if not data or data.get("type") != "comment":
                self.logger.debug(f"Invalid or non-comment data for {comment_id}")
                return None
                
            comment = HNComment(
                id=data.get("id", comment_id),
                text=data.get("text", ""),
                by=data.get("by"),
                time=data.get("time"),
                parent=data.get("parent"),
                kids=data.get("kids", [])
            )
            
            self.logger.debug(f"Fetched comment {comment_id} by {comment.by}, {len(comment.text)} chars")
            return comment
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch comment {comment_id}: {e}")
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
        self.logger = get_logger(self.__class__.__name__)
        self.logger.debug("Initialized ContentExtractor")
    
    @log_performance(get_logger("ContentExtractor.extract_content"), "content extraction")
    def extract_content(self, story: HNStory) -> ArticleContent:
        """Extract article content from a story's URL."""
        self.logger.debug(f"Extracting content for story {story.id}: '{story.title[:50]}...'")
        
        if not story.url:
            self.logger.warning(f"No URL available for story {story.id}")
            return ArticleContent(
                title=story.title,
                content="",
                url="",
                extracted_successfully=False,
                error_message="No URL available"
            )
        
        self.logger.debug(f"Fetching content from URL: {story.url}")
        
        try:
            response = self.session.get(story.url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            self.logger.debug(f"Successfully fetched {len(response.content)} bytes from {story.url}")
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Remove script and style elements
            removed_elements = len(soup(["script", "style"]))
            for element in soup(["script", "style"]):
                element.extract()
            self.logger.debug(f"Removed {removed_elements} script/style elements")
            
            # Try to find main content using selectors
            content = self._extract_main_content(soup)
            
            # Fallback to body if no main content found
            if not content:
                self.logger.debug("Main content not found, falling back to body extraction")
                content = self._extract_body_content(soup)
            
            # Clean up text
            original_length = len(content)
            content = self._clean_content(content)
            self.logger.debug(f"Cleaned content: {original_length} -> {len(content)} characters")
            
            result = ArticleContent(
                title=story.title,
                content=content,
                url=story.url,
                extracted_successfully=True
            )
            
            self.logger.info(f"Successfully extracted {len(content)} characters from {story.url}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to extract content from {story.url}: {e}")
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