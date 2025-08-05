"""
Tests for the summarizers package.
"""

from unittest.mock import patch, Mock
from hn_summarizer.models import SummarizerMode, SummarizerConfig, ArticleContent, HNComment, EnhancedSummary
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
    
    @patch('hn_summarizer.summarizers.ollama.requests.post')
    def test_enhanced_summarize_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": """ARTICLE_SUMMARY:
This article discusses AI development trends and their impact on software engineering.

COMMENT_SUMMARY: 
Community members share experiences with AI tools and debate their effectiveness.

KEY_POINTS:
1. AI is transforming software development workflows
2. Developers need to adapt to new AI-assisted tools
3. Quality concerns remain about AI-generated code

RELATED_LINKS:
1. Machine learning in software engineering
2. AI code generation tools comparison  
3. Future of programming with AI assistance"""
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        content = ArticleContent(
            title="AI in Development",
            content="AI is changing how we code...",
            url="https://example.com"
        )
        comments = [
            HNComment(id=1, by="user1", text="I use AI tools daily", time=123456),
            HNComment(id=2, by="user2", text="Quality is still a concern", time=123457)
        ]
        
        result = self.summarizer.enhanced_summarize(content, comments, 12345)
        
        assert isinstance(result, EnhancedSummary)
        assert "AI development trends" in result.article_summary
        assert "Community members" in result.comment_summary
        assert len(result.key_points) == 3
        assert "AI is transforming" in result.key_points[0]
        assert len(result.related_links) == 3
        assert "Machine learning" in result.related_links[0]
        assert result.original_url == "https://example.com"
        assert "12345" in result.hn_discussion_url
    
    @patch('hn_summarizer.summarizers.ollama.requests.post')
    def test_enhanced_summarize_fallback(self, mock_post):
        mock_post.side_effect = Exception("Connection failed")
        
        content = ArticleContent(
            title="Test Article",
            content="Test content here",
            url="https://example.com"
        )
        comments = [
            HNComment(id=1, by="user1", text="Great article!", time=123456)
        ]
        
        result = self.summarizer.enhanced_summarize(content, comments, 12345)
        
        # Should fallback to basic enhanced summary
        assert isinstance(result, EnhancedSummary)
        assert result.original_url == "https://example.com"
        assert "12345" in result.hn_discussion_url
        assert len(result.key_points) == 3
        assert len(result.related_links) == 3


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
    
    @patch('os.getenv')
    @patch('hn_summarizer.summarizers.llmapi.requests.post')
    def test_enhanced_summarize_success(self, mock_post, mock_getenv):
        mock_getenv.return_value = "test-api-key"
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": """ARTICLE_SUMMARY:
This article explores the latest developments in quantum computing technology.

COMMENT_SUMMARY:
Discussion focuses on practical applications and current limitations of quantum systems.

KEY_POINTS:
1. Quantum computing shows promise for cryptography applications
2. Current hardware limitations prevent widespread adoption
3. Major tech companies are investing heavily in quantum research

RELATED_LINKS:
1. Quantum cryptography fundamentals
2. Quantum hardware development trends
3. Commercial quantum computing applications"""
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        content = ArticleContent(
            title="Quantum Computing Advances",
            content="Recent breakthroughs in quantum technology...",
            url="https://example.com/quantum"
        )
        comments = [
            HNComment(id=1, by="researcher", text="Exciting developments in the field", time=123456),
            HNComment(id=2, by="engineer", text="Still limited by hardware constraints", time=123457)
        ]
        
        result = self.summarizer.enhanced_summarize(content, comments, 54321)
        
        assert isinstance(result, EnhancedSummary)
        assert "quantum computing technology" in result.article_summary
        assert "practical applications" in result.comment_summary
        assert len(result.key_points) == 3
        assert "cryptography applications" in result.key_points[0]
        assert len(result.related_links) == 3
        assert "Quantum cryptography" in result.related_links[0]
        assert result.original_url == "https://example.com/quantum"
        assert "54321" in result.hn_discussion_url
    
    @patch('os.getenv')
    def test_enhanced_summarize_no_api_key_fallback(self, mock_getenv):
        mock_getenv.return_value = None
        
        content = ArticleContent(
            title="Test Article",
            content="Test content here",
            url="https://example.com"
        )
        comments = [
            HNComment(id=1, by="user1", text="Interesting read", time=123456)
        ]
        
        result = self.summarizer.enhanced_summarize(content, comments, 12345)
        
        # Should fallback to basic enhanced summary
        assert isinstance(result, EnhancedSummary)
        assert result.original_url == "https://example.com"
        assert "12345" in result.hn_discussion_url
        assert len(result.key_points) == 3
        assert len(result.related_links) == 3
    
    @patch('os.getenv')
    @patch('hn_summarizer.summarizers.llmapi.requests.post')
    def test_enhanced_summarize_api_failure_fallback(self, mock_post, mock_getenv):
        mock_getenv.return_value = "test-api-key"
        mock_post.side_effect = Exception("API error")
        
        content = ArticleContent(
            title="Test Article",
            content="Test content here",
            url="https://example.com"
        )
        comments = [
            HNComment(id=1, by="user1", text="Good point", time=123456)
        ]
        
        result = self.summarizer.enhanced_summarize(content, comments, 12345)
        
        # Should fallback to basic enhanced summary
        assert isinstance(result, EnhancedSummary)
        assert result.original_url == "https://example.com"
        assert "12345" in result.hn_discussion_url
        assert len(result.key_points) == 3
        assert len(result.related_links) == 3