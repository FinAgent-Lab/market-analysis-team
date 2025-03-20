"""Tool for the RSS feed."""

from typing import Optional, Type
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.rss_feeder.rss_feeder import RSSFeederAPIWrapper


class RSSFeederInput(BaseModel):
    """Input for the RSS Feeder tool."""

    query: str = Field(description="The query to search for in the RSS feed.")


class RSSFeederTool(BaseTool):
    """Tool for the RSS Feeder."""

    name: str = "rss_feeder"
    description: str = (
        "Useful when you need to get the latest news from a specific RSS feed."
    )
    args_schema: Type[BaseModel] = RSSFeederInput

    url: str = Field(description="The URL of the RSS feed.")
    limit: int = Field(description="The number of results to return.", default=10)
    extract_content: bool = Field(
        description="Whether to extract the content of the article.", default=True
    )
    nlp: bool = Field(
        description="Whether to use NLP to extract the content of the article.",
        default=False,
    )  # This is for newspaper3k
    api_wrapper: RSSFeederAPIWrapper = Field(default_factory=RSSFeederAPIWrapper)

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        try:
            return self.api_wrapper.results(
                # query=query,
                url=self.url,
                limit=self.limit,
                extract_content=self.extract_content,
                nlp=self.nlp,
            )
        except Exception as e:
            return repr(e)

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        try:
            return await self.api_wrapper.results_async(
                # query=query,
                url=self.url,
                limit=self.limit,
                extract_content=self.extract_content,
                nlp=self.nlp,
            )
        except Exception as e:
            return repr(e)
