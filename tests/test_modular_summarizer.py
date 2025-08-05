"""
Tests for the modularized HN Summarizer structure.
"""

from unittest.mock import Mock, patch
from hn_summarizer import HackerNewsSummarizer
from hn_summarizer.models import SummarizerMode, HNStory, ArticleContent
from hn_summarizer.fetchers import HackerNewsAPI, ContentExtractor
from hn_summarizer.summarizers import BasicSummarizer


class TestModularHackerNewsSummarizer:
    
    def setup_method(self):
        self.summarizer = HackerNewsSummarizer(mode="basic")
    
    def test_init_basic_mode(self):
        assert self.summarizer.mode == SummarizerMode.BASIC
        assert isinstance(self.summarizer.api_client, HackerNewsAPI)
        assert isinstance(self.summarizer.content_extractor, ContentExtractor)
        assert isinstance(self.summarizer.summarizer, BasicSummarizer)
    
    def test_init_different_modes(self):
        from hn_summarizer.summarizers import OllamaSummarizer, LLMAPISummarizer
        
        ollama_summarizer = HackerNewsSummarizer(mode="ollama")
        assert ollama_summarizer.mode == SummarizerMode.OLLAMA
        assert isinstance(ollama_summarizer.summarizer, OllamaSummarizer)
        
        llmapi_summarizer = HackerNewsSummarizer(mode="llmapi")
        assert llmapi_summarizer.mode == SummarizerMode.LLMAPI
        assert isinstance(llmapi_summarizer.summarizer, LLMAPISummarizer)
    
    def test_get_top_stories_delegation(self):
        with patch.object(self.summarizer.api_client, 'get_top_story_ids') as mock_method:
            mock_method.return_value = [1, 2, 3]
            
            result = self.summarizer.get_top_stories(3)
            
            assert result == [1, 2, 3]
            mock_method.assert_called_once_with(3)
    
    def test_get_story_details_delegation(self):
        with patch.object(self.summarizer.api_client, 'get_story_details') as mock_method:
            mock_story = HNStory(id=123, title="Test", score=100)
            mock_method.return_value = mock_story
            
            result = self.summarizer.get_story_details(123)
            
            assert result == mock_story
            mock_method.assert_called_once_with(123)
    
    def test_extract_article_content_delegation(self):
        with patch.object(self.summarizer.content_extractor, 'extract_content') as mock_method:
            mock_story = HNStory(id=123, title="Test", url="https://example.com")
            mock_content = ArticleContent(title="Test", content="Test content", url="https://example.com")
            mock_method.return_value = mock_content
            
            result = self.summarizer.extract_article_content(mock_story)
            
            assert result == mock_content
            mock_method.assert_called_once_with(mock_story)
    
    def test_generate_summary_delegation(self):
        with patch.object(self.summarizer.summarizer, 'summarize') as mock_method:
            mock_content = ArticleContent(title="Test", content="Test content", url="https://example.com")
            mock_summary = ["Line 1", "Line 2", "Line 3"]
            mock_method.return_value = mock_summary
            
            result = self.summarizer.generate_summary(mock_content)
            
            assert result == mock_summary
            mock_method.assert_called_once_with(mock_content)
    
    @patch('time.sleep')
    def test_summarize_articles_integration(self, mock_sleep):
        # Mock the individual components
        with patch.object(self.summarizer, 'get_top_stories') as mock_get_stories, \
             patch.object(self.summarizer, 'get_story_details') as mock_get_details, \
             patch.object(self.summarizer, 'extract_article_content') as mock_extract, \
             patch.object(self.summarizer, 'generate_summary') as mock_summarize:
            
            # Setup mocks
            mock_get_stories.return_value = [1]
            mock_story = HNStory(id=1, title="Test Article", url="https://example.com", score=100)
            mock_get_details.return_value = mock_story
            
            mock_content = ArticleContent(title="Test Article", content="Test content", url="https://example.com")
            mock_extract.return_value = mock_content
            
            mock_summarize.return_value = ["Summary line 1", "Summary line 2", "Summary line 3"]
            
            # Execute
            result = self.summarizer.summarize_articles(1)
            
            # Verify
            assert len(result) == 1
            assert result[0]['id'] == 1
            assert result[0]['title'] == "Test Article"
            assert result[0]['url'] == "https://example.com"
            assert result[0]['score'] == 100
            assert result[0]['summary'] == ["Summary line 1", "Summary line 2", "Summary line 3"]
            
            # Verify method calls
            mock_get_stories.assert_called_once_with(1)
            mock_get_details.assert_called_once_with(1)
            mock_extract.assert_called_once_with(mock_story)
            mock_summarize.assert_called_once_with(mock_content)
            mock_sleep.assert_called_once()


class TestHNStoryModel:
    
    def test_hn_story_creation(self):
        story = HNStory(
            id=123,
            title="Test Article",
            url="https://example.com",
            score=100,
            by="testuser"
        )
        
        assert story.id == 123
        assert story.title == "Test Article"
        assert story.url == "https://example.com"
        assert story.score == 100
        assert story.by == "testuser"
    
    def test_hn_story_defaults(self):
        story = HNStory(id=123, title="Test")
        
        assert story.id == 123
        assert story.title == "Test"
        assert story.url is None
        assert story.score == 0
        assert story.type == "story"


class TestArticleContentModel:
    
    def test_article_content_creation(self):
        content = ArticleContent(
            title="Test Article",
            content="Test content here",
            url="https://example.com",
            extracted_successfully=True
        )
        
        assert content.title == "Test Article"
        assert content.content == "Test content here"
        assert content.url == "https://example.com"
        assert content.extracted_successfully == True
        assert content.error_message is None
    
    def test_article_content_with_error(self):
        content = ArticleContent(
            title="Test Article",
            content="",
            url="https://example.com",
            extracted_successfully=False,
            error_message="Failed to fetch"
        )
        
        assert content.extracted_successfully == False
        assert content.error_message == "Failed to fetch"