"""
Core functionality for fetching and summarizing Hacker News articles
"""

import requests
import time
import re
from typing import List, Dict, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class HackerNewsSummarizer:
    """Main class for fetching and summarizing Hacker News articles"""
    
    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_top_stories(self, limit: int = 20) -> List[int]:
        """Fetch top story IDs from Hacker News API"""
        try:
            response = self.session.get(f"{self.base_url}/topstories.json")
            response.raise_for_status()
            story_ids = response.json()[:limit]
            return story_ids
        except requests.RequestException as e:
            print(f"Error fetching top stories: {e}")
            return []
    
    def get_story_details(self, story_id: int) -> Optional[Dict]:
        """Fetch details for a specific story"""
        try:
            response = self.session.get(f"{self.base_url}/item/{story_id}.json")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching story {story_id}: {e}")
            return None
    
    def extract_article_content(self, url: str) -> str:
        """Extract article content from URL"""
        if not url:
            return ""
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Try to find main content
            content_selectors = [
                'article', '[role="main"]', '.content', '.post-content',
                '.entry-content', '.article-content', 'main', '.story-body'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text()
                    break
            
            # Fallback to body if no main content found
            if not content:
                content = soup.body.get_text() if soup.body else soup.get_text()
            
            # Clean up text
            content = re.sub(r'\s+', ' ', content).strip()
            return content[:5000]  # Limit content length
            
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return ""
    
    def generate_summary(self, title: str, content: str, url: str = "") -> List[str]:
        """Generate a 3-line summary using simple text processing"""
        if not content:
            summary_lines = [
                f"Title: {title}",
                "Content not available for summarization.",
                f"URL: {url[:80]}..." if len(url) > 80 else f"URL: {url}"
            ]
        else:
            # Simple extractive summary - take first few sentences
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            summary_lines = [
                f"Article: {title}",
                sentences[0][:120] + "..." if len(sentences) > 0 and len(sentences[0]) > 120 else sentences[0] if len(sentences) > 0 else "No content available.",
                sentences[1][:120] + "..." if len(sentences) > 1 and len(sentences[1]) > 120 else sentences[1] if len(sentences) > 1 else f"URL: {url}"
            ]
        
        return summary_lines
    
    def summarize_articles(self, limit: int = 20) -> List[Dict]:
        """Main method to fetch and summarize articles"""
        results = []
        
        story_ids = self.get_top_stories(limit)
        if not story_ids:
            return results
        
        for i, story_id in enumerate(story_ids, 1):
            print(f"Processing story {i}/{limit}: {story_id}")
            
            # Get story details
            story = self.get_story_details(story_id)
            if not story:
                continue
            
            title = story.get('title', 'No title')
            url = story.get('url', '')
            score = story.get('score', 0)
            
            # Extract article content
            content = ""
            if url:
                content = self.extract_article_content(url)
            
            # Generate summary
            summary_lines = self.generate_summary(title, content, url)
            
            results.append({
                'id': story_id,
                'title': title,
                'url': url,
                'score': score,
                'summary': summary_lines
            })
            
            # Add delay to be respectful to servers
            time.sleep(1)
        
        return results