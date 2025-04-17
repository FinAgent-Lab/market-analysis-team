"""Tool for the Alpha Vantage financial statements analysis."""

from typing import Dict, Optional, Type, Union, Any

from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.us_stock.alpha_vantage import AlphaVantageAPIWrapper


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
        "Analyzes balance sheets, income statements, and financial ratios. "
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
            response = self.llm.invoke(prompt).content.strip().upper()

            # Check if response is a valid ticker format (1-5 uppercase letters)
            import re

            if response != "UNKNOWN" and re.match(r"^[A-Z]{1,5}$", response):
                # Verify ticker exists via Alpha Vantage API
                try:
                    result = self.api_wrapper.get_company_overview(response)
                    if "error" not in result:
                        return response
                except Exception as e:
                    print(f"Error verifying ticker with Alpha Vantage: {e}")
                    # Return the ticker if it has the right format, even if API verification fails (optional)
                    return response

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
            return self._format_financial_analysis(result)
        except Exception as e:
            return f"Error analyzing financial statements: {repr(e)}"

    def _format_financial_analysis(self, analysis_data: Dict) -> str:
        """Format analysis data into readable text."""
        output = []

        # Check if there was an error
        if "balance_sheet_error" in analysis_data:
            return f"Error retrieving balance sheet data: {analysis_data['balance_sheet_error']}"

        ticker = analysis_data.get("ticker", "Unknown")
        company_name = analysis_data.get("company_name", "")

        header = f"# Financial Statement Analysis for {company_name} (Ticker: {ticker})"
        output.append(header)

        # Company profile information
        profile = analysis_data.get("profile", {})
        if profile:
            output.append("\n## Company Profile")
            # Always check if keys exist and have values
            if "Sector" in profile and profile["Sector"]:
                output.append(f"- Sector: {profile['Sector']}")
            if "Industry" in profile and profile["Industry"]:
                output.append(f"- Industry: {profile['Industry']}")
            if "Description" in profile and profile["Description"]:
                output.append(f"- Description: {profile['Description'][:300]}...")

            # Always use safe_format
            if "MarketCapitalization" in profile:
                output.append(
                    f"- Market Cap: {self.safe_format(profile['MarketCapitalization'], prefix='$')}"
                )
            if "FullTimeEmployees" in profile:
                employees = profile.get("FullTimeEmployees")
                output.append(f"- Employees: {employees if employees else 'No data'}")

            # Always check for existence and use safe_format
            if "DividendYield" in profile:
                div_yield = self.api_wrapper.safe_float_or_empty(
                    profile["DividendYield"]
                )
                if div_yield is not None:
                    output.append(
                        f"- Dividend Yield: {self.safe_format(div_yield * 100, suffix='%')}"
                    )
                else:
                    output.append("- Dividend Yield: No data")

            # Always use safe_format
            if "52WeekHigh" in profile and "52WeekLow" in profile:
                high = self.safe_format(profile["52WeekHigh"], prefix="$")
                low = self.safe_format(profile["52WeekLow"], prefix="$")
                output.append(f"- 52-Week Range: {low} - {high}")

        # Balance sheet information
        balance_sheet = analysis_data.get("balance_sheet", {}).get("annualReports", [])
        if balance_sheet and len(balance_sheet) > 0:
            output.append("\n## Balance Sheet Information")
            recent = balance_sheet[0]
            period = recent.get("fiscalDateEnding", "N/A")
            output.append(f"Reference Period: {period}")

            if "totalAssets" in recent:
                output.append(
                    f"- Total Assets: {self.safe_format(recent['totalAssets'], prefix='$')}"
                )
            if "totalCurrentAssets" in recent:
                output.append(
                    f"- Current Assets: {self.safe_format(recent['totalCurrentAssets'], prefix='$')}"
                )
            if "totalLiabilities" in recent:
                output.append(
                    f"- Total Liabilities: {self.safe_format(recent['totalLiabilities'], prefix='$')}"
                )
            if "totalCurrentLiabilities" in recent:
                output.append(
                    f"- Current Liabilities: {self.safe_format(recent['totalCurrentLiabilities'], prefix='$')}"
                )
            if "totalShareholderEquity" in recent:
                output.append(
                    f"- Total Shareholder Equity: {self.safe_format(recent['totalShareholderEquity'], prefix='$')}"
                )
            if "longTermDebt" in recent:
                output.append(
                    f"- Long-Term Debt: {self.safe_format(recent['longTermDebt'], prefix='$')}"
                )
            if "cash" in recent:
                output.append(
                    f"- Cash and Equivalents: {self.safe_format(recent['cash'], prefix='$')}"
                )

        # Income statement information
        income_statement = analysis_data.get("income_statement", {}).get(
            "annualReports", []
        )
        if income_statement and len(income_statement) > 0:
            output.append("\n## Income Statement Information")
            recent = income_statement[0]
            period = recent.get("fiscalDateEnding", "N/A")
            output.append(f"Reference Period: {period}")

            if "totalRevenue" in recent:
                output.append(
                    f"- Total Revenue: {self.safe_format(recent['totalRevenue'], prefix='$')}"
                )
            if "costOfRevenue" in recent:
                output.append(
                    f"- Cost of Revenue: {self.safe_format(recent['costOfRevenue'], prefix='$')}"
                )
            if "grossProfit" in recent:
                output.append(
                    f"- Gross Profit: {self.safe_format(recent['grossProfit'], prefix='$')}"
                )
            if "operatingExpenses" in recent:
                output.append(
                    f"- Operating Expenses: {self.safe_format(recent['operatingExpenses'], prefix='$')}"
                )
            if "operatingIncome" in recent:
                output.append(
                    f"- Operating Income: {self.safe_format(recent['operatingIncome'], prefix='$')}"
                )
            if "netIncome" in recent:
                output.append(
                    f"- Net Income: {self.safe_format(recent['netIncome'], prefix='$')}"
                )
            if "ebitda" in recent:
                output.append(
                    f"- EBITDA: {self.safe_format(recent['ebitda'], prefix='$')}"
                )

        # Cash flow information
        cash_flow = analysis_data.get("cash_flow", {}).get("annualReports", [])
        if cash_flow and len(cash_flow) > 0:
            output.append("\n## Cash Flow Information")
            recent = cash_flow[0]
            period = recent.get("fiscalDateEnding", "N/A")
            output.append(f"Reference Period: {period}")

            if "operatingCashflow" in recent:
                output.append(
                    f"- Operating Cash Flow: {self.safe_format(recent['operatingCashflow'], prefix='$')}"
                )
            if "cashflowFromInvestment" in recent:
                output.append(
                    f"- Cash Flow from Investment: {self.safe_format(recent['cashflowFromInvestment'], prefix='$')}"
                )
            if "cashflowFromFinancing" in recent:
                output.append(
                    f"- Cash Flow from Financing: {self.safe_format(recent['cashflowFromFinancing'], prefix='$')}"
                )
            if "capitalExpenditures" in recent:
                output.append(
                    f"- Capital Expenditures: {self.safe_format(recent['capitalExpenditures'], prefix='$')}"
                )
            if "dividendPayout" in recent:
                # Use safe_format to handle None values
                output.append(
                    f"- Dividend Payout: {self.safe_format(recent['dividendPayout'], prefix='$')}"
                )

        # Financial ratios from profile
        if profile:
            output.append("\n## Financial Ratios")

            if "PERatio" in profile:
                output.append(f"- P/E Ratio: {self.safe_format(profile['PERatio'])}")
            if "PEGRatio" in profile:
                output.append(f"- PEG Ratio: {self.safe_format(profile['PEGRatio'])}")
            if "PriceToBookRatio" in profile:
                output.append(
                    f"- Price to Book Ratio: {self.safe_format(profile['PriceToBookRatio'])}"
                )
            if "EPS" in profile:
                output.append(f"- EPS: {self.safe_format(profile['EPS'], prefix='$')}")

            # Use safe_float_or_empty for conversion
            if "ReturnOnEquityTTM" in profile:
                roe = self.api_wrapper.safe_float_or_empty(profile["ReturnOnEquityTTM"])
                if roe is not None:
                    output.append(
                        f"- Return on Equity (TTM): {self.safe_format(roe * 100, suffix='%')}"
                    )
                else:
                    output.append("- Return on Equity (TTM): No data")

            if "ReturnOnAssetsTTM" in profile:
                roa = self.api_wrapper.safe_float_or_empty(profile["ReturnOnAssetsTTM"])
                if roa is not None:
                    output.append(
                        f"- Return on Assets (TTM): {self.safe_format(roa * 100, suffix='%')}"
                    )
                else:
                    output.append("- Return on Assets (TTM): No data")

            if "OperatingMarginTTM" in profile:
                op_margin = self.api_wrapper.safe_float_or_empty(
                    profile["OperatingMarginTTM"]
                )
                if op_margin is not None:
                    output.append(
                        f"- Operating Margin (TTM): {self.safe_format(op_margin * 100, suffix='%')}"
                    )
                else:
                    output.append("- Operating Margin (TTM): No data")

            if "ProfitMargin" in profile:
                profit_margin = self.api_wrapper.safe_float_or_empty(
                    profile["ProfitMargin"]
                )
                if profit_margin is not None:
                    output.append(
                        f"- Profit Margin: {self.safe_format(profit_margin * 100, suffix='%')}"
                    )
                else:
                    output.append("- Profit Margin: No data")

            if "QuarterlyEarningsGrowthYOY" in profile:
                earnings_growth = self.api_wrapper.safe_float_or_empty(
                    profile["QuarterlyEarningsGrowthYOY"]
                )
                if earnings_growth is not None:
                    output.append(
                        f"- Quarterly Earnings Growth (YOY): {self.safe_format(earnings_growth * 100, suffix='%')}"
                    )
                else:
                    output.append("- Quarterly Earnings Growth (YOY): No data")

            if "QuarterlyRevenueGrowthYOY" in profile:
                revenue_growth = self.api_wrapper.safe_float_or_empty(
                    profile["QuarterlyRevenueGrowthYOY"]
                )
                if revenue_growth is not None:
                    output.append(
                        f"- Quarterly Revenue Growth (YOY): {self.safe_format(revenue_growth * 100, suffix='%')}"
                    )
                else:
                    output.append("- Quarterly Revenue Growth (YOY): No data")

        # Analysis information
        analysis = analysis_data.get("analysis", {})
        if analysis:
            output.append("\n## Financial Analysis")

            # Sector and industry
            if "sector" in analysis:
                output.append(f"- Sector: {analysis['sector']}")
            if "industry" in analysis:
                output.append(f"- Industry: {analysis['industry']}")

            # Liquidity analysis
            if "current_ratio" in analysis:
                output.append(f"- Current Ratio: {analysis['current_ratio']}")
                if "liquidity_evaluation" in analysis:
                    output.append(f"  - Evaluation: {analysis['liquidity_evaluation']}")

            # Debt analysis
            if "debt_to_equity" in analysis:
                output.append(f"- Debt to Equity Ratio: {analysis['debt_to_equity']}")
                if "debt_evaluation" in analysis:
                    output.append(f"  - Evaluation: {analysis['debt_evaluation']}")

            # Growth analysis
            if "revenue_growth" in analysis:
                output.append(f"- Revenue Growth: {analysis['revenue_growth']}")
                if "revenue_growth_evaluation" in analysis:
                    output.append(
                        f"  - Evaluation: {analysis['revenue_growth_evaluation']}"
                    )

            # Profitability analysis
            if "operating_margin" in analysis:
                output.append(f"- Operating Margin: {analysis['operating_margin']}")
                if "profitability_evaluation" in analysis:
                    output.append(
                        f"  - Evaluation: {analysis['profitability_evaluation']}"
                    )

            # Other margin metrics
            if "gross_margin" in analysis:
                output.append(f"- Gross Margin: {analysis['gross_margin']}")
            if "net_margin" in analysis:
                output.append(f"- Net Margin: {analysis['net_margin']}")

            # ROE analysis
            if "roe" in analysis:
                output.append(f"- ROE: {analysis['roe']}")
                if "roe_evaluation" in analysis:
                    output.append(f"  - Evaluation: {analysis['roe_evaluation']}")

            # Net income growth
            if "net_income_growth" in analysis:
                output.append(f"- Net Income Growth: {analysis['net_income_growth']}")

            # Market metrics
            if "market_cap" in analysis:
                output.append(f"- Market Cap: {analysis['market_cap']}")
            if "pe_ratio" in analysis:
                output.append(f"- P/E Ratio: {analysis['pe_ratio']}")
            if "pb_ratio" in analysis:
                output.append(f"- P/B Ratio: {analysis['pb_ratio']}")

        return "\n".join(output)
