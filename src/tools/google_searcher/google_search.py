"""Util that calls Google Search API.

In order to set this up, follow instructions at:
https://programmablesearchengine.google.com/
"""

import json
from typing import Dict, List
import urllib.request
import urllib.parse

import aiohttp
from langchain_core.utils import get_from_dict_or_env
from pydantic import BaseModel, ConfigDict, SecretStr, model_validator

GOOGLE_API_URL = "https://www.googleapis.com/customsearch/v1"

class GoogleSearchAPIWrapper(BaseModel):
    """Wrapper for Google Custom Search API."""

    google_api_key: SecretStr
    google_cse_id: SecretStr

    model_config = ConfigDict(
        extra="forbid",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and cse id exist in environment."""
        google_api_key = get_from_dict_or_env(
            values, "google_api_key", "GOOGLE_API_KEY"
        )
        google_cse_id = get_from_dict_or_env(
            values, "google_cse_id", "GOOGLE_CSE_ID"
        )
        values["google_api_key"] = google_api_key
        values["google_cse_id"] = google_cse_id

        return values

    def raw_results(
        self,
        query: str,
    ) -> Dict:
        """Get raw results from the Google Custom Search API."""
        api_key = self.google_api_key.get_secret_value()
        cse_id = self.google_cse_id.get_secret_value()

        params = {"key": api_key, "cx": cse_id, "q": query}

        # Create a request with the URL and parameters
        url = f"{GOOGLE_API_URL}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url)

        try:
            with urllib.request.urlopen(request) as response:
                response_code = response.getcode()
                if response_code == 200:
                    return json.loads(response.read().decode("utf-8"))
                else:
                    raise Exception(f"Error Code: {response_code}")
        except urllib.error.HTTPError as e:
            raise Exception(f"Error Code: {e.code}, Reason: {e.reason}")

    def results(
        self,
        query: str,
    ) -> List[Dict]:
        """Run query through Google Search and return cleaned results.

        Args:
            query: The query to search for.

        Returns:
            A list of dictionaries containing the cleaned search results.
        """
        raw_search_results = self.raw_results(query)
        if "items" not in raw_search_results:
            return []
        return self.clean_results(raw_search_results["items"])

    async def raw_results_async(
        self,
        query: str,
    ) -> Dict:
        """Get results from the Google Custom Search API asynchronously."""
        api_key = self.google_api_key.get_secret_value()
        cse_id = self.google_cse_id.get_secret_value()

        params = {"key": api_key, "cx": cse_id, "q": query}

        async with aiohttp.ClientSession() as session:
            async with session.get(GOOGLE_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.text()
                    return json.loads(data)
                else:
                    raise Exception(f"Error {response.status}: {response.reason}")

    async def results_async(
        self,
        query: str,
    ) -> List[Dict]:
        """Get cleaned results from Google Custom Search API asynchronously."""
        results_json = await self.raw_results_async(
            query=query,
        )
        if "items" not in results_json:
            return []
        return self.clean_results(results_json["items"])

    def clean_results(self, results: List[Dict]) -> List[Dict]:
        """Clean results from Google Custom Search API."""
        clean_results = []
        for result in results:
            clean_result = {
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "description": result.get("snippet", ""),
            }

            # Add optional fields if they exist
            if "pagemap" in result and "metatags" in result["pagemap"]:
                for metatag in result["pagemap"]["metatags"]:
                    if "og:site_name" in metatag:
                        clean_result["source"] = metatag["og:site_name"]
                    if "article:published_time" in metatag:
                        clean_result["pubDate"] = metatag["article:published_time"]

            clean_results.append(clean_result)
        return clean_results
