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
from .logging_config import get_logger, log_performance


class HackerNewsSummarizer:
    """Main class for fetching and summarizing Hacker News articles"""

    def __init__(self, mode: str = "basic", ollama_model: str = None, allow_fallback: bool = True):
        self.mode = SummarizerMode(mode)
        self.ollama_model = ollama_model
        self.allow_fallback = allow_fallback
        self.logger = get_logger(self.__class__.__name__)
        
        self.logger.debug(f"Initializing HackerNewsSummarizer with mode: {mode}")
        self.api_client = HackerNewsAPI()
        self.content_extractor = ContentExtractor()
        self.summarizer = self._create_summarizer()
        self.logger.info(f"HackerNewsSummarizer initialized successfully with {self.mode.value} mode")

    def _create_summarizer(self):
        """Create appropriate summarizer based on mode."""
        config = SummarizerConfig(mode=self.mode, ollama_model=self.ollama_model, allow_fallback=self.allow_fallback)
        
        self.logger.debug(f"Creating summarizer for mode: {self.mode.value}")
        
        if self.mode == SummarizerMode.BASIC:
            summarizer = BasicSummarizer(config)
        elif self.mode == SummarizerMode.OLLAMA:
            summarizer = OllamaSummarizer(config)
            self.logger.debug(f"Using Ollama model: {config.ollama_model or 'default'}")
        elif self.mode == SummarizerMode.LLMAPI:
            summarizer = LLMAPISummarizer(config)
        else:
            # Fallback to basic
            self.logger.warning(f"Unknown mode {self.mode}, falling back to basic")
            summarizer = BasicSummarizer(config)
        
        self.logger.debug(f"Summarizer created: {summarizer.__class__.__name__}")
        return summarizer

    @log_performance(get_logger("HackerNewsSummarizer.get_top_stories"), "fetching top story IDs")
    def get_top_stories(self, limit: int = 20) -> List[int]:
        """Fetch top story IDs from Hacker News API"""
        self.logger.debug(f"Fetching top {limit} story IDs from HN API")
        story_ids = self.api_client.get_top_story_ids(limit)
        self.logger.info(f"Retrieved {len(story_ids)} story IDs")
        return story_ids

    def get_story_details(self, story_id: int):
        """Fetch details for a specific story"""
        self.logger.debug(f"Fetching details for story {story_id}")
        story = self.api_client.get_story_details(story_id)
        if story:
            self.logger.debug(f"Retrieved story: {story.title[:50]}...")
        else:
            self.logger.warning(f"Failed to retrieve story {story_id}")
        return story

    def extract_article_content(self, story):
        """Extract article content from story"""
        self.logger.debug(f"Extracting content for story {story.id}: {story.title[:50]}...")
        content = self.content_extractor.extract_content(story)
        if content.extracted_successfully:
            self.logger.debug(f"Successfully extracted {len(content.content)} characters of content")
        else:
            self.logger.warning(f"Failed to extract content: {content.error_message}")
        return content

    def generate_summary(self, content) -> List[str]:
        """Generate a summary using the configured summarizer"""
        self.logger.debug(f"Generating summary using {self.summarizer.__class__.__name__}")
        summary = self.summarizer.summarize(content)
        self.logger.debug(f"Generated {len(summary)} summary lines")
        return summary

    @log_performance(get_logger("HackerNewsSummarizer.summarize_articles"), "article summarization")
    def summarize_articles(self, limit: int = 20) -> List[Dict]:
        """Main method to fetch and summarize articles"""
        self.logger.info(f"Starting summarization of {limit} articles using {self.mode.value} mode")
        results: List[Dict] = []
        successful_articles = 0
        failed_articles = 0

        story_ids = self.get_top_stories(limit)
        if not story_ids:
            self.logger.error("No story IDs retrieved from HN API")
            return results
        
        self.logger.info(f"Processing {len(story_ids)} stories")

        for i, story_id in enumerate(story_ids, 1):
            self.logger.info(f"Processing story {i}/{len(story_ids)}: {story_id}")
            print(f"Processing story {i}/{limit}: {story_id}")
            
            article_start_time = time.time()

            try:
                # For enhanced modes (ollama/llmapi), get story with comments
                if self.mode in [SummarizerMode.OLLAMA, SummarizerMode.LLMAPI]:
                    self.logger.debug(f"Fetching story {story_id} with comments for enhanced mode")
                    story_with_comments = self.api_client.get_story_with_comments(
                        story_id, MAX_COMMENTS_TO_FETCH
                    )
                    if not story_with_comments:
                        self.logger.warning(f"Failed to fetch story {story_id} with comments")
                        failed_articles += 1
                        continue
                
                    story, comments = story_with_comments
                    self.logger.debug(f"Story {story_id} has {len(comments)} comments")
                    content = self.extract_article_content(story)
                    
                    # Generate enhanced summary
                    if hasattr(self.summarizer, 'enhanced_summarize'):
                        self.logger.debug(f"Generating enhanced summary for story {story_id}")
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
                    self.logger.debug(f"Processing story {story_id} in basic mode")
                    story = self.get_story_details(story_id)
                    if not story:
                        self.logger.warning(f"Failed to fetch story {story_id}")
                        failed_articles += 1
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
                
                successful_articles += 1
                article_time = time.time() - article_start_time
                self.logger.debug(f"Successfully processed story {story_id} in {article_time:.2f}s")
                
            except Exception as e:
                failed_articles += 1
                self.logger.error(f"Failed to process story {story_id}: {e}", exc_info=True)
                continue

            # Add delay to be respectful to servers
            self.logger.debug(f"Waiting {RATE_LIMIT_DELAY}s before next request")
            time.sleep(RATE_LIMIT_DELAY)

        self.logger.info(f"Summarization complete: {successful_articles} successful, {failed_articles} failed")
        return results
    
    def _format_enhanced_summary_for_output(self, enhanced_summary: EnhancedSummary) -> List[str]:
        """Format enhanced summary for CLI output compatibility."""
        return [
            f"Article: {enhanced_summary.article_summary}",
            f"Discussion: {enhanced_summary.comment_summary}",
            f"Key Points: {' | '.join(enhanced_summary.key_points[:2])}"
        ]
