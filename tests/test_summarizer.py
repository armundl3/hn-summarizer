"""
Unit tests for the HackerNewsSummarizer class
"""

import requests
from unittest.mock import Mock, patch
from hn_summarizer.summarizer import HackerNewsSummarizer


class TestHackerNewsSummarizer:
    def setup_method(self):
        self.summarizer = HackerNewsSummarizer(mode="basic")

    def test_init(self):
        expected_url = "https://hacker-news.firebaseio.com/v0"
        assert self.summarizer.base_url == expected_url
        assert self.summarizer.mode == "basic"
        assert isinstance(self.summarizer.session, requests.Session)
        assert "User-Agent" in self.summarizer.session.headers

    def test_init_with_mode(self):
        summarizer_ollama = HackerNewsSummarizer(mode="ollama")
        assert summarizer_ollama.mode == "ollama"

        summarizer_llmapi = HackerNewsSummarizer(mode="llmapi")
        assert summarizer_llmapi.mode == "llmapi"

    @patch("hn_summarizer.summarizer.requests.Session.get")
    def test_get_top_stories_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.summarizer.get_top_stories(5)

        assert result == [1, 2, 3, 4, 5]
        expected_url = f"{self.summarizer.base_url}/topstories.json"
        mock_get.assert_called_once_with(expected_url)

    @patch("hn_summarizer.summarizer.requests.Session.get")
    def test_get_top_stories_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network error")

        result = self.summarizer.get_top_stories(5)

        assert result == []

    @patch("hn_summarizer.summarizer.requests.Session.get")
    def test_get_story_details_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": 123,
            "title": "Test Article",
            "url": "https://example.com",
            "score": 100,
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.summarizer.get_story_details(123)

        assert result["id"] == 123
        assert result["title"] == "Test Article"
        assert result["url"] == "https://example.com"
        assert result["score"] == 100
        expected_url = f"{self.summarizer.base_url}/item/123.json"
        mock_get.assert_called_once_with(expected_url)

    @patch("hn_summarizer.summarizer.requests.Session.get")
    def test_get_story_details_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network error")

        result = self.summarizer.get_story_details(123)

        assert result is None

    def test_extract_article_content_empty_url(self):
        result = self.summarizer.extract_article_content("")
        assert result == ""

        result = self.summarizer.extract_article_content(None)
        assert result == ""

    @patch("hn_summarizer.summarizer.requests.Session.get")
    def test_extract_article_content_success(self, mock_get):
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <body>
                <article>
                    <h1>Test Title</h1>
                    <p>This is the main content of the article.
                    It contains useful information.</p>
                    <p>This is another paragraph with more details.</p>
                </article>
                <script>console.log('should be removed');</script>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.summarizer.extract_article_content("https://example.com")

        assert "Test Title" in result
        assert "main content" in result
        assert "should be removed" not in result
        mock_get.assert_called_once_with("https://example.com", timeout=10)

    @patch("hn_summarizer.summarizer.requests.Session.get")
    def test_extract_article_content_fallback_to_body(self, mock_get):
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <body>
                <div>Some content without article tags</div>
                <p>More content here</p>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.summarizer.extract_article_content("https://example.com")

        assert "Some content without article tags" in result
        assert "More content here" in result

    @patch("hn_summarizer.summarizer.requests.Session.get")
    def test_extract_article_content_exception(self, mock_get):
        mock_get.side_effect = Exception("Connection error")

        result = self.summarizer.extract_article_content("https://example.com")

        assert result == ""

    def test_generate_summary_with_content(self):
        title = "Test Article Title"
        content = (
            "This is the first sentence. This is the second sentence "
            "with more details. Third sentence here."
        )
        url = "https://example.com"

        result = self.summarizer.generate_summary(title, content, url)

        assert len(result) == 3
        assert result[0] == f"Article: {title}"
        assert "first sentence" in result[1]
        assert "second sentence" in result[2]

    def test_generate_summary_without_content(self):
        title = "Test Article Title"
        content = ""
        url = "https://example.com"

        result = self.summarizer.generate_summary(title, content, url)

        assert len(result) == 3
        assert result[0] == f"Title: {title}"
        assert "Content not available" in result[1]
        assert url in result[2]

    def test_generate_summary_long_url(self):
        title = "Test Article Title"
        content = ""
        url = "https://example.com/" + "a" * 100

        result = self.summarizer.generate_summary(title, content, url)

        assert "..." in result[2]
        assert len(result[2]) < len(url)

    def test_generate_summary_short_sentences(self):
        title = "Test Article Title"
        content = "Short. Very short sentence. Another one."
        url = "https://example.com"

        result = self.summarizer.generate_summary(title, content, url)

        assert len(result) == 3
        assert result[0] == f"Article: {title}"

    @patch.object(HackerNewsSummarizer, "get_top_stories")
    @patch.object(HackerNewsSummarizer, "get_story_details")
    @patch.object(HackerNewsSummarizer, "extract_article_content")
    @patch("time.sleep")
    def test_summarize_articles_success(
        self, mock_sleep, mock_extract, mock_get_story, mock_get_stories
    ):
        mock_get_stories.return_value = [1, 2]
        mock_get_story.side_effect = [
            {
                "id": 1,
                "title": "Article 1",
                "url": "https://example1.com",
                "score": 100,
            },
            {
                "id": 2,
                "title": "Article 2",
                "url": "https://example2.com",
                "score": 200,
            },
        ]
        mock_extract.side_effect = ["Content 1", "Content 2"]

        result = self.summarizer.summarize_articles(2)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["title"] == "Article 1"
        assert result[0]["score"] == 100
        assert len(result[0]["summary"]) == 3
        assert result[1]["id"] == 2
        assert result[1]["title"] == "Article 2"
        assert result[1]["score"] == 200
        assert len(result[1]["summary"]) == 3

        assert mock_sleep.call_count == 2

    @patch.object(HackerNewsSummarizer, "get_top_stories")
    def test_summarize_articles_no_stories(self, mock_get_stories):
        mock_get_stories.return_value = []

        result = self.summarizer.summarize_articles(5)

        assert result == []

    @patch.object(HackerNewsSummarizer, "get_top_stories")
    @patch.object(HackerNewsSummarizer, "get_story_details")
    @patch("time.sleep")
    def test_summarize_articles_story_details_none(
        self, mock_sleep, mock_get_story, mock_get_stories
    ):
        mock_get_stories.return_value = [1, 2]
        mock_get_story.side_effect = [
            None,
            {
                "id": 2,
                "title": "Article 2",
                "url": "https://example2.com",
                "score": 200,
            },
        ]

        with patch.object(
            self.summarizer,
            "extract_article_content",
            return_value="Content 2",
        ):
            result = self.summarizer.summarize_articles(2)

        assert len(result) == 1
        assert result[0]["id"] == 2

    @patch.object(HackerNewsSummarizer, "get_top_stories")
    @patch.object(HackerNewsSummarizer, "get_story_details")
    @patch.object(HackerNewsSummarizer, "extract_article_content")
    @patch("time.sleep")
    def test_summarize_articles_no_url(
        self, mock_sleep, mock_extract, mock_get_story, mock_get_stories
    ):
        mock_get_stories.return_value = [1]
        mock_get_story.return_value = {
            "id": 1,
            "title": "Article 1",
            "score": 100,
        }

        result = self.summarizer.summarize_articles(1)

        assert len(result) == 1
        assert result[0]["url"] == ""
        mock_extract.assert_not_called()

    def test_generate_summary_mode_routing(self):
        title = "Test Article"
        content = "Test content"
        # Test basic mode
        basic_summarizer = HackerNewsSummarizer(mode="basic")
        result = basic_summarizer.generate_summary(title, content)
        assert len(result) == 3
        assert result[0].startswith("Article:")

        # Test ollama mode (should fallback to basic without ollama)
        ollama_summarizer = HackerNewsSummarizer(mode="ollama")
        result = ollama_summarizer.generate_summary(title, content)
        assert len(result) == 3

        # Test llmapi mode (should fallback to basic without API key)
        llmapi_summarizer = HackerNewsSummarizer(mode="llmapi")
        result = llmapi_summarizer.generate_summary(title, content)
        assert len(result) == 3

    @patch("hn_summarizer.summarizer.requests.post")
    def test_ollama_mode_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Line 1\nLine 2\nLine 3"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        ollama_summarizer = HackerNewsSummarizer(mode="ollama")
        result = ollama_summarizer._generate_ollama_summary(
            "Test Title", "Test content"
        )

        assert len(result) == 3
        assert result[0] == "Line 1"
        assert result[1] == "Line 2"
        assert result[2] == "Line 3"

    @patch("hn_summarizer.summarizer.requests.post")
    def test_ollama_mode_fallback(self, mock_post):
        mock_post.side_effect = Exception("Connection failed")

        ollama_summarizer = HackerNewsSummarizer(mode="ollama")
        result = ollama_summarizer._generate_ollama_summary(
            "Test Title", "Test content"
        )

        # Should fallback to basic mode
        assert len(result) == 3
        assert result[0].startswith("Article:")

    @patch("os.getenv")
    @patch("hn_summarizer.summarizer.requests.post")
    def test_llmapi_mode_success(self, mock_post, mock_getenv):
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

        llmapi_summarizer = HackerNewsSummarizer(mode="llmapi")
        result = llmapi_summarizer._generate_llmapi_summary(
            "Test Title", "Test content"
        )

        assert len(result) == 3
        assert result[0] == "API Line 1"
        assert result[1] == "API Line 2"
        assert result[2] == "API Line 3"

    @patch("os.getenv")
    def test_llmapi_mode_no_api_key(self, mock_getenv):
        mock_getenv.return_value = None

        llmapi_summarizer = HackerNewsSummarizer(mode="llmapi")
        result = llmapi_summarizer._generate_llmapi_summary(
            "Test Title", "Test content"
        )

        # Should fallback to basic mode
        assert len(result) == 3
        assert result[0].startswith("Article:")
