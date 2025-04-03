"""Tool for the Google Custom Search API."""

from typing import Dict, List, Optional, Type, Union

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.google_searcher.google_search import GoogleSearchAPIWrapper


class GoogleInput(BaseModel):
    """Input for the Google Custom Search tool."""

    query: str = Field(description="search query to look up")


class GoogleSearchResults(BaseTool):
    """Tool that queries the Google Custom Search API and gets back json.

    Setup:
        Set environment variables ``GOOGLE_SEARCH_API_KEY`` and ``SEARCH_ENGINE_ID``.

        .. code-block:: bash

            export GOOGLE_SEARCH_API_KEY="your-search-api-key"
            export SEARCH_ENGINE_ID="your-custom-search-engine-id"

    Instantiate:

        .. code-block:: python

            tool = GoogleSearchResults()

    Invoke:

        .. code-block:: python

            tool.invoke({'query': '미국 증시 정보'})  # info search for US stock market
    """

    name: str = "google_search_results_json"
    description: str = (
        "A search engine for US stock market using google search API. "
        "Useful for when you need to answer questions about US stock prices, news, info, estimation, etc. "
        "Input should be a search query in Korean or English."
    )
    args_schema: Type[BaseModel] = GoogleInput

    api_wrapper: GoogleSearchAPIWrapper = Field(default_factory=GoogleSearchAPIWrapper)

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Union[List[Dict], str]:
        """Use the tool."""
        try:
            return self.api_wrapper.results(query)
        except Exception as e:
            return repr(e)

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Union[List[Dict], str]:
        """Use the tool asynchronously."""
        try:
            return await self.api_wrapper.results_async(query)
        except Exception as e:
            return repr(e)


class GoogleSearch(GoogleSearchResults):
    """Tool specialized for Google search."""

    name: str = "google_search"
    description: str = (
        "A search engine for US stock market using google search API. "
        "Useful for when you need to answer questions about US stock prices, news, info, estimation, etc. "
        "Input should be a search query in Korean or English."
    )
