"""
Tests for the fetchers module.
"""

import requests
from unittest.mock import Mock, patch
from hn_summarizer.fetchers import HackerNewsAPI, ContentExtractor
from hn_summarizer.models import HNStory


class TestHackerNewsAPI:
    
    def setup_method(self):
        self.api = HackerNewsAPI()
    
    @patch('hn_summarizer.fetchers.requests.Session.get')
    def test_get_top_story_ids_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.api.get_top_story_ids(5)
        
        assert result == [1, 2, 3, 4, 5]
        mock_get.assert_called_once()
    
    @patch('hn_summarizer.fetchers.requests.Session.get')
    def test_get_top_story_ids_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network error")
        
        result = self.api.get_top_story_ids(5)
        
        assert result == []
    
    @patch('hn_summarizer.fetchers.requests.Session.get')
    def test_get_story_details_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": 123,
            "title": "Test Article",
            "url": "https://example.com",
            "score": 100,
            "by": "testuser",
            "time": 1234567890,
            "type": "story"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.api.get_story_details(123)
        
        assert isinstance(result, HNStory)
        assert result.id == 123
        assert result.title == "Test Article"
        assert result.url == "https://example.com"
        assert result.score == 100
        assert result.by == "testuser"
    
    @patch('hn_summarizer.fetchers.requests.Session.get')
    def test_get_story_details_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network error")
        
        result = self.api.get_story_details(123)
        
        assert result is None


class TestContentExtractor:
    
    def setup_method(self):
        self.extractor = ContentExtractor()
    
    def test_extract_content_no_url(self):
        story = HNStory(id=123, title="Test Article")
        
        result = self.extractor.extract_content(story)
        
        assert result.title == "Test Article"
        assert result.content == ""
        assert result.url == ""
        assert result.extracted_successfully == False
        assert "No URL available" in result.error_message
    
    @patch('hn_summarizer.fetchers.requests.Session.get')
    def test_extract_content_success(self, mock_get):
        story = HNStory(id=123, title="Test Article", url="https://example.com")
        
        mock_response = Mock()
        mock_response.content = b'''
        <html>
            <body>
                <article>
                    <h1>Test Title</h1>
                    <p>This is the main content.</p>
                </article>
                <script>Should be removed</script>
            </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.extractor.extract_content(story)
        
        assert result.title == "Test Article"
        assert "Test Title" in result.content
        assert "main content" in result.content
        assert "Should be removed" not in result.content
        assert result.url == "https://example.com"
        assert result.extracted_successfully == True
    
    @patch('hn_summarizer.fetchers.requests.Session.get')
    def test_extract_content_error(self, mock_get):
        story = HNStory(id=123, title="Test Article", url="https://example.com")
        mock_get.side_effect = Exception("Connection failed")
        
        result = self.extractor.extract_content(story)
        
        assert result.title == "Test Article"
        assert result.content == ""
        assert result.extracted_successfully == False
        assert "Connection failed" in result.error_message