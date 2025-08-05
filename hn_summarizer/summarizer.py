"""
Core functionality for fetching and summarizing Hacker News articles
"""

import requests
import time
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


class HackerNewsSummarizer:
    """Main class for fetching and summarizing Hacker News articles"""

    def __init__(self, mode: str = "basic"):
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.mode = mode
        self.session = requests.Session()
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36"
        )
        self.session.headers.update({"User-Agent": user_agent})

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
            url = f"{self.base_url}/item/{story_id}.json"
            response = self.session.get(url)
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

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Try to find main content
            content_selectors = [
                "article",
                '[role="main"]',
                ".content",
                ".post-content",
                ".entry-content",
                ".article-content",
                "main",
                ".story-body",
            ]

            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text()
                    break

            # Fallback to body if no main content found
            if not content:
                if soup.body:
                    content = soup.body.get_text()
                else:
                    content = soup.get_text()

            # Clean up text
            content = re.sub(r"\s+", " ", content).strip()
            return content[:5000]  # Limit content length

        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return ""

    def generate_summary(
        self, title: str, content: str, url: str = ""
    ) -> List[str]:
        """Generate a 3-line summary based on the configured mode"""
        if self.mode == "basic":
            return self._generate_basic_summary(title, content, url)
        elif self.mode == "ollama":
            return self._generate_ollama_summary(title, content, url)
        elif self.mode == "llmapi":
            return self._generate_llmapi_summary(title, content, url)
        else:
            return self._generate_basic_summary(title, content, url)

    def _generate_basic_summary(
        self, title: str, content: str, url: str = ""
    ) -> List[str]:
        """Generate a 3-line summary using simple text processing"""
        if not content:
            summary_lines = [
                f"Title: {title}",
                "Content not available for summarization.",
                f"URL: {url[:80]}..." if len(url) > 80 else f"URL: {url}",
            ]
        else:
            # Simple extractive summary - take first few sentences
            sentences = re.split(r"[.!?]+", content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

            summary_lines = [
                f"Article: {title}",
                sentences[0][:120] + "..."
                if len(sentences) > 0 and len(sentences[0]) > 120
                else sentences[0]
                if len(sentences) > 0
                else "No content available.",
                sentences[1][:120] + "..."
                if len(sentences) > 1 and len(sentences[1]) > 120
                else sentences[1]
                if len(sentences) > 1
                else f"URL: {url}",
            ]

        return summary_lines

    def _generate_ollama_summary(
        self, title: str, content: str, url: str = ""
    ) -> List[str]:
        """Generate a 3-line summary using Ollama local LLM"""
        if not content:
            return self._generate_basic_summary(title, content, url)

        try:
            import requests as ollama_requests

            ollama_url = "http://localhost:11434/api/generate"
            prompt = f"""Summarize the following article in exactly 3 lines:

Title: {title}
Content: {content[:2000]}

Provide a concise 3-line summary:"""

            payload = {
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "max_tokens": 200}
            }

            response = ollama_requests.post(
                ollama_url, json=payload, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            summary_text = result.get("response", "").strip()

            if summary_text:
                lines = summary_text.split('\n')
                # Clean and filter lines
                lines = [line.strip() for line in lines if line.strip()]
                # Ensure we have exactly 3 lines
                if len(lines) >= 3:
                    return lines[:3]
                elif len(lines) > 0:
                    # Pad with basic info if needed
                    while len(lines) < 3:
                        if len(lines) == 1:
                            lines.append(f"Source: {title}")
                        else:
                            lines.append(f"URL: {url}")
                    return lines[:3]

        except Exception as e:
            print(f"Ollama summarization failed: {e}")
            print("Falling back to basic summarization...")

        # Fallback to basic summary
        return self._generate_basic_summary(title, content, url)

    def _generate_llmapi_summary(
        self, title: str, content: str, url: str = ""
    ) -> List[str]:
        """Generate a 3-line summary using external LLM API"""
        if not content:
            return self._generate_basic_summary(title, content, url)

        try:
            import os
            import requests as api_requests

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("OPENAI_API_KEY not found, falling back to basic mode")
                return self._generate_basic_summary(title, content, url)

            api_url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""Summarize the following article in exactly 3 lines:

Title: {title}
Content: {content[:2000]}

Please provide exactly 3 concise lines that capture the key points."""

            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }

            response = api_requests.post(
                api_url, headers=headers, json=payload, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            summary_text = result["choices"][0]["message"]["content"].strip()

            if summary_text:
                lines = summary_text.split('\n')
                # Clean and filter lines
                lines = [line.strip() for line in lines if line.strip()]
                # Ensure we have exactly 3 lines
                if len(lines) >= 3:
                    return lines[:3]
                elif len(lines) > 0:
                    # Pad with basic info if needed
                    while len(lines) < 3:
                        if len(lines) == 1:
                            lines.append(f"Source: {title}")
                        else:
                            lines.append(f"URL: {url}")
                    return lines[:3]

        except Exception as e:
            print(f"LLM API summarization failed: {e}")
            print("Falling back to basic summarization...")

        # Fallback to basic summary
        return self._generate_basic_summary(title, content, url)

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

            title = story.get("title", "No title")
            url = story.get("url", "")
            score = story.get("score", 0)

            # Extract article content
            content = ""
            if url:
                content = self.extract_article_content(url)

            # Generate summary
            summary_lines = self.generate_summary(title, content, url)

            results.append(
                {
                    "id": story_id,
                    "title": title,
                    "url": url,
                    "score": score,
                    "summary": summary_lines,
                }
            )

            # Add delay to be respectful to servers
            time.sleep(1)

        return results
