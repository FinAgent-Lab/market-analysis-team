import json
import urllib.request
import urllib.parse
from typing import Dict, List

import aiohttp
import numpy as np
from langchain_core.utils import get_from_dict_or_env
from pydantic import BaseModel, ConfigDict, SecretStr, model_validator
from langchain_openai import OpenAIEmbeddings

GOOGLE_API_URL = "https://www.googleapis.com/customsearch/v1"


class GoogleSearchAPIWrapper(BaseModel):
    """Wrapper for Google Custom Search API with relevance filtering using embeddings."""

    google_api_key: SecretStr
    google_cse_id: SecretStr

    model_config = ConfigDict(
        extra="forbid",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: Dict) -> Dict:
        google_api_key = get_from_dict_or_env(
            values, "google_api_key", "GOOGLE_API_KEY"
        )
        google_cse_id = get_from_dict_or_env(values, "google_cse_id", "GOOGLE_CSE_ID")
        values["google_api_key"] = google_api_key
        values["google_cse_id"] = google_cse_id
        return values

    def raw_results(
        self,
        query: str,
    ) -> Dict:
        api_key = self.google_api_key.get_secret_value()
        cse_id = self.google_cse_id.get_secret_value()

        params = {"key": api_key, "cx": cse_id, "q": query}
        url = f"{GOOGLE_API_URL}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url)

        try:
            with urllib.request.urlopen(request) as response:
                if response.getcode() == 200:
                    return json.loads(response.read().decode("utf-8"))
                raise Exception(f"Error Code: {response.getcode()}")
        except urllib.error.HTTPError as e:
            raise Exception(f"Error Code: {e.code}, Reason: {e.reason}")

    def results(
        self,
        query: str,
    ) -> List[Dict]:
        raw = self.raw_results(query)
        if "items" not in raw:
            return []
        return self.clean_results(raw["items"])

    async def raw_results_async(
        self,
        query: str,
    ) -> Dict:
        api_key = self.google_api_key.get_secret_value()
        cse_id = self.google_cse_id.get_secret_value()
        params = {"key": api_key, "cx": cse_id, "q": query}
        async with aiohttp.ClientSession() as session:
            async with session.get(GOOGLE_API_URL, params=params) as response:
                if response.status == 200:
                    return json.loads(await response.text())
                raise Exception(f"Error {response.status}: {response.reason}")

    async def results_async(
        self,
        query: str,
    ) -> List[Dict]:
        raw = await self.raw_results_async(query)
        if "items" not in raw:
            return []
        return self.clean_results(raw["items"])

    def clean_results(self, results: List[Dict]) -> List[Dict]:
        clean = []
        for r in results:
            item = {
                "title": r.get("title", ""),
                "link": r.get("link", ""),
                "description": r.get("snippet", ""),
            }
            if "pagemap" in r and "metatags" in r["pagemap"]:
                for m in r["pagemap"]["metatags"]:
                    if "og:site_name" in m:
                        item["source"] = m["og:site_name"]
                    if "article:published_time" in m:
                        item["pubDate"] = m["article:published_time"]
            clean.append(item)
        return clean

    def filtered_results(
        self,
        query: str,
        embedding_model: str = "text-embedding-3-small",
        top_n: int = 15,
    ) -> List[Dict]:
        """Retrieve and rank search results by semantic similarity to the query."""
        # 1) Retrieve base results
        results = self.results(query)
        if not isinstance(results, list) or not results:
            return []
        # 2) Prepare descriptions and filter empties
        descriptions = [r.get("description", "") for r in results]
        valid_indices = [i for i, desc in enumerate(descriptions) if desc]
        if not valid_indices:
            return []
        valid_desc = [descriptions[i] for i in valid_indices]
        valid_res = [results[i] for i in valid_indices]
        # 3) Embed
        embedder = OpenAIEmbeddings(model=embedding_model)
        desc_embs = embedder.embed_documents(valid_desc)
        query_emb = embedder.embed_query(query)
        q_np = np.array(query_emb)
        # 4) Compute cosine similarities
        sims = []
        for d in desc_embs:
            d_np = np.array(d)
            denom = np.linalg.norm(d_np) * np.linalg.norm(q_np)
            sims.append((float(np.dot(d_np, q_np) / denom) if denom > 0 else 0.0))
        # 5) Select top_n
        top_idxs = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:top_n]
        return [valid_res[i] for i in top_idxs]

    async def filtered_results_async(
        self,
        query: str,
        embedding_model: str = "text-embedding-3-small",
        top_n: int = 15,
    ) -> List[Dict]:
        """Async version of filtered_results."""
        results = await self.results_async(query)
        if not isinstance(results, list) or not results:
            return []
        descriptions = [r.get("description", "") for r in results]
        valid_indices = [i for i, desc in enumerate(descriptions) if desc]
        if not valid_indices:
            return []
        valid_desc = [descriptions[i] for i in valid_indices]
        valid_res = [results[i] for i in valid_indices]
        embedder = OpenAIEmbeddings(model=embedding_model)
        desc_embs = embedder.embed_documents(valid_desc)
        query_emb = embedder.embed_query(query)
        q_np = np.array(query_emb)
        sims = []
        for d in desc_embs:
            d_np = np.array(d)
            denom = np.linalg.norm(d_np) * np.linalg.norm(q_np)
            sims.append((float(np.dot(d_np, q_np) / denom) if denom > 0 else 0.0))
        top_idxs = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:top_n]
        return [valid_res[i] for i in top_idxs]
