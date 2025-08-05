"""
Core functionality for fetching and summarizing Hacker News articles
"""

import time
from typing import List, Dict

from .config import RATE_LIMIT_DELAY
from .models import SummarizerMode, SummarizerConfig, ArticleSummary, EnhancedSummary
from .fetchers import HackerNewsAPI, ContentExtractor
from .summarizers import BasicSummarizer, OllamaSummarizer, LLMAPISummarizer
from .config import MAX_COMMENTS_TO_FETCH


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

            # For enhanced modes (ollama/llmapi), get story with comments
            if self.mode in [SummarizerMode.OLLAMA, SummarizerMode.LLMAPI]:
                story_with_comments = self.api_client.get_story_with_comments(
                    story_id, MAX_COMMENTS_TO_FETCH
                )
                if not story_with_comments:
                    continue
                
                story, comments = story_with_comments
                content = self.extract_article_content(story)
                
                # Generate enhanced summary
                if hasattr(self.summarizer, 'enhanced_summarize'):
                    enhanced_summary = self.summarizer.enhanced_summarize(content, comments, story_id)
                    summary_lines = self._format_enhanced_summary_for_output(enhanced_summary)
                else:
                    summary_lines = self.generate_summary(content)
                
                results.append({
                    "id": story.id,
                    "title": story.title,
                    "url": story.url or "",
                    "score": story.score,
                    "summary": summary_lines,
                    "enhanced": enhanced_summary if hasattr(self.summarizer, 'enhanced_summarize') else None
                })
            else:
                # Basic mode - use original logic
                story = self.get_story_details(story_id)
                if not story:
                    continue

                content = self.extract_article_content(story)
                summary_lines = self.generate_summary(content)

                results.append({
                    "id": story.id,
                    "title": story.title,
                    "url": story.url or "",
                    "score": story.score,
                    "summary": summary_lines,
                })

            # Add delay to be respectful to servers
            time.sleep(RATE_LIMIT_DELAY)

        return results
    
    def _format_enhanced_summary_for_output(self, enhanced_summary: EnhancedSummary) -> List[str]:
        """Format enhanced summary for CLI output compatibility."""
        return [
            f"Article: {enhanced_summary.article_summary}",
            f"Discussion: {enhanced_summary.comment_summary}",
            f"Key Points: {' | '.join(enhanced_summary.key_points[:2])}"
        ]
