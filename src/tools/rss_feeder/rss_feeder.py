"""Util that calls RSS Feed API.

In order to set this up, you need to have an RSS feed URL.
"""

from typing import Dict, List, Literal, Optional

import aiohttp
import feedparser
from pydantic import BaseModel, ConfigDict


class RSSFeederAPIWrapper(BaseModel):
    """Wrapper for RSS Feeder API."""

    model_config = ConfigDict(
        extra="forbid",
    )

    def raw_results(
        self,
        url: str,
        limit: Optional[int] = 10,
    ) -> Dict:
        """Get raw results from the RSS Feed."""
        try:
            feed = feedparser.parse(url)
            entries = feed.entries[:limit] if limit else feed.entries
            return {"items": entries, "feed_info": feed.feed}
        except Exception as e:
            raise Exception(f"Error fetching RSS feed: {str(e)}")

    def results(
        self,
        url: str,
        limit: Optional[int] = 10,
        extract_content: Optional[bool] = False,
        nlp: Optional[bool] = False,
        extractor: str = "newspaper",  # "newspaper" 또는 "goose"
    ) -> List[Dict]:
        """Run query through RSS Feed and return cleaned results.

        Args:
            url: The URL of the RSS feed.
            limit: The number of results to return.
            extract_content: Whether to extract full article content.
            nlp: Whether to perform NLP processing (for newspaper3k).
            extractor: Which extractor to use ("newspaper" or "goose").

        Returns:
            A list of dictionaries containing the cleaned feed entries.
        """
        raw_feed_results = self.raw_results(
            url,
            limit=limit,
        )
        return self.clean_results(
            raw_feed_results["items"],
            extract_content=extract_content,
            nlp=nlp,
            extractor=extractor,
        )

    async def raw_results_async(
        self,
        feed_url: str,
        limit: Optional[int] = 10,
    ) -> Dict:
        """Get results from the RSS Feed asynchronously."""

        async def fetch() -> str:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url) as response:
                    if response.status == 200:
                        data = await response.text()
                        return data
                    else:
                        raise Exception(f"Error {response.status}: {response.reason}")

        try:
            feed_content = await fetch()
            feed = feedparser.parse(feed_content)
            entries = feed.entries[:limit] if limit else feed.entries
            return {"items": entries, "feed_info": feed.feed}
        except Exception as e:
            raise Exception(f"Error fetching RSS feed asynchronously: {str(e)}")

    async def results_async(
        self,
        feed_url: str,
        limit: Optional[int] = 10,
        extract_content: Optional[bool] = False,
        nlp: Optional[bool] = False,
    ) -> List[Dict]:
        """Get cleaned results from RSS Feed asynchronously."""
        results_json = await self.raw_results_async(
            feed_url=feed_url,
            limit=limit,
            nlp=nlp,
        )
        return self.clean_results(
            results_json["items"], extract_content=extract_content, nlp=nlp
        )

    def extract_article_content_goose(self, url: str) -> Dict:
        """Extract article content using Goose3.

        Args:
            url: The URL of the article to extract content from.

        Returns:
            A dictionary containing the extracted article content.
        """
        try:
            from goose3 import Goose
            from goose3.configuration import Configuration

            config = Configuration()
            config.browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

            with Goose(config) as g:
                article = g.extract(url=url)
                return {
                    "title": article.title,
                    # TODO: Get the content of the article
                    "cleaned_text": article.cleaned_text,
                    "meta_description": article.meta_description,
                    "meta_keywords": article.meta_keywords,
                    "publish_date": article.publish_date,
                    "authors": article.authors,
                    "top_image": article.top_image.src if article.top_image else None,
                    "movies": [m.src for m in article.movies] if article.movies else [],
                }
        except Exception as e:
            return {
                "error": f"Error extracting article content with Goose3: {str(e)}",
                "title": "",
                "cleaned_text": "",
            }

    def extract_article_content_newspaper(self, url: str, nlp: bool = False) -> Dict:
        """Extract article content using newspaper3k.

        Args:
            url: The URL of the article to extract content from.
            nlp: Whether to perform NLP processing (summary and keyword extraction).

        Returns:
            A dictionary containing the extracted article content.
        """

        try:
            from newspaper import Article

            article = Article(url)
            article.download()
            article.parse()

            if nlp:
                article.nlp()

            return {
                "title": article.title,
                # TODO: Get the content of the article
                "text": article.text,
                "summary": article.summary if nlp else "",
                "keywords": article.keywords if nlp else [],
                "publish_date": article.publish_date,
                "authors": article.authors,
                "top_image": article.top_image,
                "movies": article.movies,
                "language": article.meta_lang,
            }
        except Exception as e:
            return {
                "error": f"Error extracting article content with newspaper3k: {str(e)}",
                "title": "",
                "text": "",
            }

    def clean_results(
        self,
        results: List[Dict],
        extract_content: bool = False,
        nlp: bool = False,
        extractor: Literal[
            "newspaper", "goose"
        ] = "goose",  # select "newspaper" or "goose"
    ) -> List[Dict]:
        """Clean results from RSS Feed."""
        clean_results = []
        for result in results:
            clean_result = {
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "description": result.get("description", ""),
                "published": result.get("published", ""),
            }

            # Add optional fields if they exist
            for field in ["author", "tags", "id"]:
                if field in result:
                    clean_result[field] = result[field]

            # Extract full article content if requested
            if extract_content and clean_result["link"]:
                if extractor == "newspaper":
                    article_content = self.extract_article_content_newspaper(
                        clean_result["link"], nlp=nlp
                    )
                else:  # goose
                    article_content = self.extract_article_content_goose(
                        clean_result["link"]
                    )
                clean_result["article_content"] = article_content

            clean_results.append(clean_result)
        return clean_results
