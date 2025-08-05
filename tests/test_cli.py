"""
Unit tests for the CLI functionality
"""

from click.testing import CliRunner
from unittest.mock import Mock, patch
from hn_summarizer.cli import main


class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()

    @patch("hn_summarizer.cli.HackerNewsSummarizer")
    def test_main_default_parameters(self, mock_summarizer_class):
        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_articles.return_value = [
            {
                "id": 1,
                "title": "Test Article",
                "url": "https://example.com",
                "score": 100,
                "summary": ["Line 1", "Line 2", "Line 3"],
            }
        ]

        result = self.runner.invoke(main)

        assert result.exit_code == 0
        mock_summarizer_class.assert_called_once_with(mode="basic")
        mock_summarizer.summarize_articles.assert_called_once_with(20)
        assert "Fetching top 20 Hacker News articles..." in result.output
        assert "--- Article 1 (Score: 100) ---" in result.output
        assert "Line 1" in result.output
        assert "Line 2" in result.output
        assert "Line 3" in result.output
        assert "Summary generation complete!" in result.output

    @patch("hn_summarizer.cli.HackerNewsSummarizer")
    def test_main_custom_count(self, mock_summarizer_class):
        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_articles.return_value = [
            {
                "id": 1,
                "title": "Test Article",
                "url": "https://example.com",
                "score": 100,
                "summary": ["Line 1", "Line 2", "Line 3"],
            }
        ]

        result = self.runner.invoke(main, ["--count", "5"])

        assert result.exit_code == 0
        mock_summarizer.summarize_articles.assert_called_once_with(5)
        assert "Fetching top 5 Hacker News articles..." in result.output

    @patch("hn_summarizer.cli.HackerNewsSummarizer")
    def test_main_short_option_count(self, mock_summarizer_class):
        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_articles.return_value = []

        result = self.runner.invoke(main, ["-c", "10"])

        assert result.exit_code == 0
        mock_summarizer.summarize_articles.assert_called_once_with(10)
        assert "Fetching top 10 Hacker News articles..." in result.output

    def test_main_invalid_count_too_low(self):
        result = self.runner.invoke(main, ["--count", "0"])

        assert result.exit_code != 0
        assert "Invalid value for" in result.output

    def test_main_invalid_count_too_high(self):
        result = self.runner.invoke(main, ["--count", "101"])

        assert result.exit_code != 0
        assert "Invalid value for" in result.output

    @patch("hn_summarizer.cli.HackerNewsSummarizer")
    def test_main_output_to_file(self, mock_summarizer_class):
        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_articles.return_value = [
            {
                "id": 1,
                "title": "Test Article",
                "url": "https://example.com",
                "score": 100,
                "summary": ["Line 1", "Line 2", "Line 3"],
            }
        ]

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(main, ["--output", "test_output.txt"])

            assert result.exit_code == 0

            with open("test_output.txt", "r") as f:
                content = f.read()
                assert "--- Article 1 (Score: 100) ---" in content
                assert "Line 1" in content
                assert "Line 2" in content
                assert "Line 3" in content
                assert "Summary generation complete!" in content

    @patch("hn_summarizer.cli.HackerNewsSummarizer")
    def test_main_short_option_output(self, mock_summarizer_class):
        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_articles.return_value = []

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(main, ["-o", "test_output.txt"])

            assert result.exit_code == 0

            with open("test_output.txt", "r") as f:
                content = f.read()
                assert "No articles found." in content
                assert "Summary generation complete!" not in content

    @patch("hn_summarizer.cli.HackerNewsSummarizer")
    def test_main_combined_options(self, mock_summarizer_class):
        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_articles.return_value = []

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                main, ["-c", "3", "-o", "combined_output.txt"]
            )

            assert result.exit_code == 0
            mock_summarizer.summarize_articles.assert_called_once_with(3)

            with open("combined_output.txt", "r") as f:
                content = f.read()
                assert "No articles found." in content
                assert "Summary generation complete!" not in content

    @patch("hn_summarizer.cli.HackerNewsSummarizer")
    def test_main_no_articles_found(self, mock_summarizer_class):
        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_articles.return_value = []

        result = self.runner.invoke(main)

        assert result.exit_code == 0
        assert "No articles found." in result.output
        assert "Summary generation complete!" not in result.output

    @patch("hn_summarizer.cli.HackerNewsSummarizer")
    def test_main_multiple_articles(self, mock_summarizer_class):
        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_articles.return_value = [
            {
                "id": 1,
                "title": "First Article",
                "url": "https://example1.com",
                "score": 100,
                "summary": ["First Line 1", "First Line 2", "First Line 3"],
            },
            {
                "id": 2,
                "title": "Second Article",
                "url": "https://example2.com",
                "score": 200,
                "summary": ["Second Line 1", "Second Line 2", "Second Line 3"],
            },
        ]

        result = self.runner.invoke(main)

        assert result.exit_code == 0
        assert "--- Article 1 (Score: 100) ---" in result.output
        assert "--- Article 2 (Score: 200) ---" in result.output
        assert "First Line 1" in result.output
        assert "Second Line 1" in result.output

    @patch("hn_summarizer.cli.HackerNewsSummarizer")
    def test_main_article_without_summary_lines(self, mock_summarizer_class):
        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_articles.return_value = [
            {
                "id": 1,
                "title": "Test Article",
                "url": "https://example.com",
                "score": 100,
                "summary": [],
            }
        ]

        result = self.runner.invoke(main)

        assert result.exit_code == 0
        assert "--- Article 1 (Score: 100) ---" in result.output
        assert "Summary generation complete!" in result.output

    @patch("hn_summarizer.cli.HackerNewsSummarizer")
    def test_main_with_mode_option(self, mock_summarizer_class):
        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_articles.return_value = []

        result = self.runner.invoke(main, ["--mode", "ollama"])

        assert result.exit_code == 0
        mock_summarizer_class.assert_called_once_with(mode="ollama")

    @patch("hn_summarizer.cli.HackerNewsSummarizer")
    def test_main_with_mode_short_option(self, mock_summarizer_class):
        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer
        mock_summarizer.summarize_articles.return_value = []

        result = self.runner.invoke(main, ["-m", "llmapi"])

        assert result.exit_code == 0
        mock_summarizer_class.assert_called_once_with(mode="llmapi")

    def test_help_option(self):
        result = self.runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Fetch and summarize top Hacker News articles" in result.output
        assert "--count" in result.output
        assert "--output" in result.output
        assert "--mode" in result.output
