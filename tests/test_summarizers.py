"""
Tests for the summarizers package.
"""

from unittest.mock import patch, Mock
from hn_summarizer.models import SummarizerMode, SummarizerConfig, ArticleContent
from hn_summarizer.summarizers import BasicSummarizer, OllamaSummarizer, LLMAPISummarizer


class TestBasicSummarizer:
    
    def setup_method(self):
        config = SummarizerConfig(mode=SummarizerMode.BASIC)
        self.summarizer = BasicSummarizer(config)
    
    def test_summarize_with_content(self):
        content = ArticleContent(
            title="Test Article",
            content="This is the first sentence. This is the second sentence with more details. Third sentence here.",
            url="https://example.com"
        )
        
        result = self.summarizer.summarize(content)
        
        assert len(result) == 3
        assert result[0] == "Article: Test Article"
        assert "first sentence" in result[1]
        assert "second sentence" in result[2]
    
    def test_summarize_without_content(self):
        content = ArticleContent(
            title="Test Article",
            content="",
            url="https://example.com"
        )
        
        result = self.summarizer.summarize(content)
        
        assert len(result) == 3
        assert result[0] == "Title: Test Article"
        assert "Content not available" in result[1]
        assert "https://example.com" in result[2]
    
    def test_summarize_long_url(self):
        long_url = "https://example.com/" + "a" * 100
        content = ArticleContent(
            title="Test Article",
            content="",
            url=long_url
        )
        
        result = self.summarizer.summarize(content)
        
        assert len(result) == 3
        assert "..." in result[2]
        assert len(result[2]) < len(long_url)


class TestOllamaSummarizer:
    
    def setup_method(self):
        config = SummarizerConfig(mode=SummarizerMode.OLLAMA)
        self.summarizer = OllamaSummarizer(config)
    
    def test_summarize_without_content_fallback(self):
        content = ArticleContent(
            title="Test Article",
            content="",
            url="https://example.com"
        )
        
        result = self.summarizer.summarize(content)
        
        assert len(result) == 3
        assert result[0] == "Title: Test Article"
        assert "Content not available" in result[1]
    
    @patch('hn_summarizer.summarizers.ollama.requests.post')
    def test_summarize_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Line 1 summary\nLine 2 summary\nLine 3 summary"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        content = ArticleContent(
            title="Test Article",
            content="Test content here",
            url="https://example.com"
        )
        
        result = self.summarizer.summarize(content)
        
        assert len(result) == 3
        assert result[0] == "Line 1 summary"
        assert result[1] == "Line 2 summary"
        assert result[2] == "Line 3 summary"
    
    @patch('hn_summarizer.summarizers.ollama.requests.post')
    def test_summarize_failure_fallback(self, mock_post):
        mock_post.side_effect = Exception("Connection failed")
        
        content = ArticleContent(
            title="Test Article", 
            content="Test content here",
            url="https://example.com"
        )
        
        result = self.summarizer.summarize(content)
        
        # Should fallback to basic summarization
        assert len(result) == 3
        assert result[0] == "Article: Test Article"


class TestLLMAPISummarizer:
    
    def setup_method(self):
        config = SummarizerConfig(mode=SummarizerMode.LLMAPI)
        self.summarizer = LLMAPISummarizer(config)
    
    def test_summarize_without_content_fallback(self):
        content = ArticleContent(
            title="Test Article",
            content="",
            url="https://example.com"
        )
        
        result = self.summarizer.summarize(content)
        
        assert len(result) == 3
        assert result[0] == "Title: Test Article"
        assert "Content not available" in result[1]
    
    @patch('os.getenv')
    def test_summarize_no_api_key_fallback(self, mock_getenv):
        mock_getenv.return_value = None
        
        content = ArticleContent(
            title="Test Article",
            content="Test content here", 
            url="https://example.com"
        )
        
        result = self.summarizer.summarize(content)
        
        # Should fallback to basic summarization
        assert len(result) == 3
        assert result[0] == "Article: Test Article"
    
    @patch('os.getenv')
    @patch('hn_summarizer.summarizers.llmapi.requests.post')
    def test_summarize_success(self, mock_post, mock_getenv):
        mock_getenv.return_value = "test-api-key"
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "API Line 1\nAPI Line 2\nAPI Line 3"
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        content = ArticleContent(
            title="Test Article",
            content="Test content here",
            url="https://example.com"
        )
        
        result = self.summarizer.summarize(content)
        
        assert len(result) == 3
        assert result[0] == "API Line 1"
        assert result[1] == "API Line 2" 
        assert result[2] == "API Line 3"
    
    @patch('os.getenv')
    @patch('hn_summarizer.summarizers.llmapi.requests.post')
    def test_summarize_api_failure_fallback(self, mock_post, mock_getenv):
        mock_getenv.return_value = "test-api-key"
        mock_post.side_effect = Exception("API error")
        
        content = ArticleContent(
            title="Test Article",
            content="Test content here",
            url="https://example.com"
        )
        
        result = self.summarizer.summarize(content)
        
        # Should fallback to basic summarization
        assert len(result) == 3
        assert result[0] == "Article: Test Article"