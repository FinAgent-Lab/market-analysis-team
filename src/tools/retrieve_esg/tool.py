"""Tool for ESG data retrieval."""

from typing import Optional, Type, Dict, Any, List
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.retrieve_esg.retrieve_esg import ESGSearchWrapper


class ESGDataInput(BaseModel):
    """Input for the ESG Data tool."""

    ticker: str = Field(description="The stock ticker symbol to get ESG data for.")
    force_refresh: bool = Field(
        description="Whether to force refresh data from yfinance.", default=False
    )


class ESGDataTool(BaseTool):
    """Tool for retrieving ESG (Environmental, Social, Governance) data for stocks."""

    name: str = "esg_data"
    description: str = (
        "Useful when you need to get ESG (Environmental, Social, Governance) "
        "ratings and scores for publicly traded companies. "
        "Input should be a valid stock ticker symbol."
    )
    args_schema: Type[BaseModel] = ESGDataInput

    api_wrapper: ESGSearchWrapper = Field(default_factory=ESGSearchWrapper)

    def _run(
        self,
        ticker: str,
        force_refresh: bool = False,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Use the tool."""
        try:
            # 동기 메서드 사용
            result = self.api_wrapper.get_esg_data_sync(
                ticker=ticker,
                force_refresh=force_refresh,
            )
            return result
        except Exception as e:
            return {"error": repr(e)}

    async def _arun(
        self,
        ticker: str,
        force_refresh: bool = False,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Use the tool asynchronously."""
        try:
            # 비동기 메서드 사용
            result = await self.api_wrapper.get_esg_data_async(
                ticker=ticker,
                force_refresh=force_refresh,
            )
            return result
        except Exception as e:
            return {"error": repr(e)}
