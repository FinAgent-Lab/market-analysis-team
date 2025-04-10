from typing import Dict, List, Optional, Type, Union
from typing_extensions import Literal

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.alpha_searcher.alpha_search import AlphaSearchWrapper

class AlphaSearch(BaseModel):
    """Input for the Alpha Search tool."""

    query: str = Field(description="search query to look up")


class AlphaSearchResults(BaseTool):
    '''
    description
    '''
    
    description: str = ""
    
    ticker: str = "AAPL"
    search_type: str = "report"
    
    api_wrapper: AlphaSearchWrapper = Field(default_factory=AlphaSearchWrapper)
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Union[List[Dict], str]:
        """Use the tool."""
        try:
            return self.api_wrapper.run(
                query,
                ticker = self.ticker,
                search_type=self.search_type,
            )
        except Exception as e:
            return repr(e)

    async def _run(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Union[List[Dict], str]:
        """Use the tool asynchronously."""
        try:
            return await self.api_wrapper.run(
                query,
                ticker = self.ticker,
                search_type=self.search_type,
            )
        except Exception as e:
            return repr(e)

class AlphaUrlSearch(AlphaSearchResults):
    """Tool specialized for Alpha report search."""

    name: str = "alpha_urls_search"
    description: str = (
        "This tool is for crawling report urls"
    )
    search_type: str = "url"
    
class AlphaReportSearch(AlphaSearchResults):
    """Tool specialized for Alpha report search."""

    name: str = "alpha_report_search"
    description: str = (
        "This tool is for crawling report scripts"
    )
    search_type: str = "report"