"""Tool for the Alpha Vantage financial statements analysis."""

from typing import Dict, Optional, Type, Union, Any

from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.us_stock.alpha_vantage_client import AlphaVantageAPIWrapper
from src.tools.us_stock import format_financial_analysis


class USStockInput(BaseModel):
    """Input for the US financial statement analysis tool."""

    query: str = Field(
        description="query containing company name or US stock ticker symbol (e.g., Apple, AAPL, Microsoft, MSFT)"
    )


class USFinancialStatementTool(BaseTool):
    """Tool that analyzes financial statements of US stocks using Alpha Vantage."""

    name: str = "us_financial_statement_analyzer"
    description: str = (
        "A tool for analyzing financial statements of US stocks using Alpha Vantage. "
        "Analyzes balance sheets, income statements, and financial ratios with "
        "focus on profitability and stability metrics. "
        "Input can be a company name (e.g., Apple, Microsoft) or a US stock ticker symbol (e.g., AAPL, MSFT)."
    )
    args_schema: Type[BaseModel] = USStockInput
    api_wrapper: AlphaVantageAPIWrapper = Field(default_factory=AlphaVantageAPIWrapper)

    # Set llm property as private to exclude from Pydantic validation
    _llm = None

    @property
    def llm(self):
        return self._llm

    @llm.setter
    def llm(self, value):
        self._llm = value

    def safe_format(
        self, value: Any, prefix: str = "", suffix: str = "", decimal_places: int = 2
    ) -> str:
        """
        Safely format financial values.
        Returns 'No data' for None or 'None' values.
        """
        if (
            value is None
            or value == ""
            or value == "None"
            or (isinstance(value, str) and value.strip().lower() == "none")
        ):
            return "No data"
        try:
            float_val = self.api_wrapper.safe_float_or_empty(value)
            if float_val is None:
                return "No data"

            formatted = f"{float_val:,.{decimal_places}f}"
            return f"{prefix}{formatted}{suffix}"
        except (ValueError, TypeError):
            return "No data"

    def _extract_ticker(self, query: str) -> Optional[str]:
        """Extract ticker from query using LLM inference and validate with Alpha Vantage API."""
        # Return None if no LLM is available
        if self.llm is None:
            print("LLM is not available")
            return None

        # Ask LLM to convert company name to ticker
        prompt = f"""
        Identify the US stock market ticker symbol for the company mentioned in this query:
        "{query}"
        
        Rules:
        1. Only output the ticker symbol (e.g., AAPL, MSFT, GOOGL) without any explanation.
        2. If multiple companies are mentioned, choose the most prominent one.
        3. If no company can be clearly identified, output "UNKNOWN".
        4. US stock tickers are typically 1-5 capital letters.
        
        Ticker:
        """

        try:
            # Query LLM - use .invoke instead of .predict
            print(f"Querying LLM with prompt for: {query}")
            response = self.llm.invoke(prompt)
            ticker = response.content.strip().upper()
            print(f"Extracted ticker: {ticker}")

            # Check if response is a valid ticker format (1-5 uppercase letters)
            import re

            if ticker != "UNKNOWN" and re.match(r"^[A-Z]{1,5}$", ticker):
                print(f"Valid ticker format: {ticker}")
                # Verify ticker exists via Alpha Vantage API
                try:
                    print(f"Verifying ticker with Alpha Vantage: {ticker}")
                    result = self.api_wrapper.get_company_overview(ticker)
                    if "error" not in result:
                        print(f"Ticker verified: {ticker}")
                        return ticker
                    else:
                        print(
                            f"Ticker verification failed: {result.get('error', 'Unknown error')}"
                        )
                except Exception as e:
                    print(f"Error verifying ticker with Alpha Vantage: {e}")
                    # Return the ticker if it has the right format, even if API verification fails
                    return ticker
            else:
                print(f"Invalid ticker format or 'UNKNOWN': {ticker}")

            return None
        except Exception as e:
            print(f"Error querying LLM for ticker extraction: {e}")
            return None

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Union[Dict, str]:
        """Run the tool."""
        try:
            ticker = self._extract_ticker(query)
            if not ticker:
                return "No valid ticker symbol found in the query. Please provide a query with a company name or US stock ticker (e.g., Apple, AAPL, Microsoft, MSFT)."

            # Get analysis from the API wrapper
            result = self.api_wrapper.analyze_financial_statements(ticker)

            # Format results for readability
            return format_financial_analysis(result)
        except Exception as e:
            import traceback

            print(f"Error analyzing financial statements: {repr(e)}")
            print(traceback.format_exc())
            return f"Error analyzing financial statements: {repr(e)}"
