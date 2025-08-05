"""
Core functionality for fetching and summarizing Hacker News articles
"""

import time
from typing import List, Dict

from .config import RATE_LIMIT_DELAY
from .models import SummarizerMode, SummarizerConfig, ArticleSummary
from .fetchers import HackerNewsAPI, ContentExtractor
from .summarizers import BasicSummarizer, OllamaSummarizer, LLMAPISummarizer


class HackerNewsSummarizer:
    """Main class for fetching and summarizing Hacker News articles"""

    def __init__(self, mode: str = "basic"):
        self.mode = SummarizerMode(mode)
        self.api_client = HackerNewsAPI()
        self.content_extractor = ContentExtractor()
        self.summarizer = self._create_summarizer()

    def _create_summarizer(self):
        """Create appropriate summarizer based on mode."""
        config = SummarizerConfig(mode=self.mode)
        
        if self.mode == SummarizerMode.BASIC:
            return BasicSummarizer(config)
        elif self.mode == SummarizerMode.OLLAMA:
            return OllamaSummarizer(config)
        elif self.mode == SummarizerMode.LLMAPI:
            return LLMAPISummarizer(config)
        else:
            # Fallback to basic
            return BasicSummarizer(config)

    def get_top_stories(self, limit: int = 20) -> List[int]:
        """Fetch top story IDs from Hacker News API"""
        return self.api_client.get_top_story_ids(limit)

    def get_story_details(self, story_id: int):
        """Fetch details for a specific story"""
        return self.api_client.get_story_details(story_id)

    def extract_article_content(self, story):
        """Extract article content from story"""
        return self.content_extractor.extract_content(story)

    def generate_summary(self, content) -> List[str]:
        """Generate a summary using the configured summarizer"""
        return self.summarizer.summarize(content)

    def summarize_articles(self, limit: int = 20) -> List[Dict]:
        """Main method to fetch and summarize articles"""
        results: List[Dict] = []

        story_ids = self.get_top_stories(limit)
        if not story_ids:
            return results

        for i, story_id in enumerate(story_ids, 1):
            print(f"Processing story {i}/{limit}: {story_id}")

            # Get story details
            story = self.get_story_details(story_id)
            if not story:
                continue

            # Extract article content
            content = self.extract_article_content(story)

            # Generate summary
            summary_lines = self.generate_summary(content)

            results.append(
                {
                    "id": story.id,
                    "title": story.title,
                    "url": story.url or "",
                    "score": story.score,
                    "summary": summary_lines,
                }
            )

            # Add delay to be respectful to servers
            time.sleep(RATE_LIMIT_DELAY)

        return results
