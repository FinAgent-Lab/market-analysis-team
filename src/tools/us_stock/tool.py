"""Tool for the Alpha Vantage financial statements analysis."""

from typing import Dict, Optional, Type, Union, Tuple
from datetime import datetime
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.us_stock.alpha_vantage_client import AlphaVantageAPIWrapper
from src.tools.us_stock import format_financial_analysis


class USStockInput(BaseModel):
    """Enhanced input for US financial statement analysis with date support."""

    query: str = Field(
        description="Query containing company name/ticker and optionally a specific date. "
                    "Examples: 'Apple', 'AAPL as of 2023-12-31', 'Microsoft in Q2 2023', "
                    "'Tesla financial health in December 2022', 'NVDA 2023년 말 기준'"
    )


class USFinancialStatementTool(BaseTool):
    """Enhanced tool with date extraction and historical analysis."""

    name: str = "us_financial_statement_analyzer"
    description: str = (
        "Analyzes US stock financial statements with support for historical backtesting. "
        "Can analyze current data or data as of a specific date mentioned in the query. "
        "Supports various date formats and Korean language. "
        "Examples: 'Apple', 'AAPL as of 2023-12-31', 'Microsoft in Q2 2023'"
    )
    args_schema: Type[BaseModel] = USStockInput
    api_wrapper: AlphaVantageAPIWrapper = Field(default_factory=AlphaVantageAPIWrapper)

    _llm = None

    @property
    def llm(self):
        return self._llm

    @llm.setter
    def llm(self, value):
        self._llm = value

    def _extract_ticker_and_date(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract both ticker symbol and analysis date from query."""
        if self.llm is None:
            print("LLM is not available")
            return None, None

        prompt = f"""
        Extract the ticker symbol and analysis date from this financial query:
        "{query}"
        
        Instructions:
        1. Identify the US stock ticker (1-5 capital letters like AAPL, MSFT, GOOGL)
        2. Identify any specific date mentioned
        3. Convert company names to tickers (Apple→AAPL, Microsoft→MSFT, etc.)
        4. Convert date expressions to YYYY-MM-DD format
        
        Date conversion examples:
        - "Q1 2023" → "2023-03-31" (end of Q1)
        - "Q2 2023" → "2023-06-30" (end of Q2)  
        - "Q3 2023" → "2023-09-30" (end of Q3)
        - "Q4 2023" → "2023-12-31" (end of Q4)
        - "December 2022" → "2022-12-31"
        - "2023년 말" → "2023-12-31"
        - "as of 2023-12-31" → "2023-12-31"
        
        Return format: TICKER|DATE or TICKER|CURRENT
        - Use "CURRENT" if no specific date is mentioned
        - Use exact YYYY-MM-DD format for dates
        
        Examples:
        - "Apple as of 2023-12-31" → AAPL|2023-12-31
        - "MSFT in Q2 2023" → MSFT|2023-06-30
        - "Tesla 2022년 말 기준" → TSLA|2022-12-31
        - "NVDA" → NVDA|CURRENT
        
        Output only the result in TICKER|DATE format:
        """

        try:
            response = self.llm.invoke(prompt)
            result = response.content.strip().upper()

            if "|" in result:
                ticker, date = result.split("|", 1)

                # Validate ticker format
                import re
                if re.match(r"^[A-Z]{1,5}$", ticker):
                    # Validate date format if not CURRENT
                    if date == "CURRENT":
                        return ticker, None
                    else:
                        try:
                            # Validate date format
                            datetime.strptime(date, '%Y-%m-%d')
                            return ticker, date
                        except ValueError:
                            print(f"Invalid date format: {date}")
                            return ticker, None
                else:
                    print(f"Invalid ticker format: {ticker}")
                    return None, None
            else:
                print(f"Invalid response format: {result}")
                return None, None

        except Exception as e:
            print(f"Error extracting ticker and date: {e}")
            return None, None

    def _filter_data_by_date(self, data: Dict, target_date: str, report_type: str = "annualReports") -> Dict:
        """Filter financial data to get the most recent report before or on target date."""
        if "error" in data or report_type not in data:
            return data

        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        reports = data[report_type]

        # Find the most recent report on or before target date
        valid_reports = []
        for report in reports:
            if "fiscalDateEnding" in report:
                try:
                    report_date = datetime.strptime(report["fiscalDateEnding"], '%Y-%m-%d')
                    if report_date <= target_dt:
                        valid_reports.append((report, report_date))
                except ValueError:
                    continue

        if valid_reports:
            # Sort by date (most recent first) and take the top one
            valid_reports.sort(key=lambda x: x[1], reverse=True)
            most_recent_report = valid_reports[0][0]

            # Return data with only the most relevant report
            filtered_data = data.copy()
            filtered_data[report_type] = [most_recent_report]
            return filtered_data
        else:
            # No data available for that date
            filtered_data = data.copy()
            filtered_data[report_type] = []
            filtered_data["date_filter_warning"] = f"No financial data available as of {target_date}"
            return filtered_data

    def _get_historical_data(self, ticker: str, target_date: str) -> Dict:
        """Get financial data as of a specific date."""
        print(f"Fetching historical data for {ticker} as of {target_date}")

        result = {"ticker": ticker, "analysis_date": target_date, "historical_analysis": True}

        # Get all financial statements
        try:
            balance_sheet = self.api_wrapper.get_balance_sheet(ticker)
            if "error" not in balance_sheet:
                result["balance_sheet"] = self._filter_data_by_date(balance_sheet, target_date, "annualReports")
                # Also get quarterly data if available
                quarterly_bs = self._filter_data_by_date(balance_sheet, target_date, "quarterlyReports")
                if quarterly_bs.get("quarterlyReports"):
                    result["balance_sheet_quarterly"] = quarterly_bs
            else:
                result["balance_sheet_error"] = balance_sheet.get("error")
        except Exception as e:
            result["balance_sheet_error"] = str(e)

        try:
            income_statement = self.api_wrapper.get_income_statement(ticker)
            if "error" not in income_statement:
                result["income_statement"] = self._filter_data_by_date(income_statement, target_date, "annualReports")
                quarterly_is = self._filter_data_by_date(income_statement, target_date, "quarterlyReports")
                if quarterly_is.get("quarterlyReports"):
                    result["income_statement_quarterly"] = quarterly_is
            else:
                result["income_statement_error"] = income_statement.get("error")
        except Exception as e:
            result["income_statement_error"] = str(e)

        try:
            cash_flow = self.api_wrapper.get_cash_flow(ticker)
            if "error" not in cash_flow:
                result["cash_flow"] = self._filter_data_by_date(cash_flow, target_date, "annualReports")
                quarterly_cf = self._filter_data_by_date(cash_flow, target_date, "quarterlyReports")
                if quarterly_cf.get("quarterlyReports"):
                    result["cash_flow_quarterly"] = quarterly_cf
            else:
                result["cash_flow_error"] = cash_flow.get("error")
        except Exception as e:
            result["cash_flow_error"] = str(e)

        # Get company overview (current data, but note it's for historical context)
        try:
            overview = self.api_wrapper.get_company_overview(ticker)
            if "error" not in overview:
                result["profile"] = overview
                result["company_name"] = overview.get("Name", "")
            else:
                result["profile_error"] = overview.get("error")
        except Exception as e:
            result["profile_error"] = str(e)

        # Analyze the historical data
        from . import analyze_financial_data
        result["analysis"] = analyze_financial_data(self.api_wrapper, result)

        return result

    def _run(
            self,
            query: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Union[Dict, str]:
        """Run the tool with date extraction support."""
        try:
            # Extract ticker and date from query
            ticker, analysis_date = self._extract_ticker_and_date(query)

            if not ticker:
                return "No valid ticker symbol found in the query. Please provide a company name or US stock ticker."

            print(f"Extracted - Ticker: {ticker}, Date: {analysis_date}")

            if analysis_date:
                # Historical analysis
                print(f"Performing historical analysis for {ticker} as of {analysis_date}")
                result = self._get_historical_data(ticker, analysis_date)

                # Format with historical context
                formatted_result = format_financial_analysis(result)
                return f"📊 **Historical Financial Analysis: {ticker} as of {analysis_date}**\n\n{formatted_result}\n\n*Note: This analysis reflects data available as of {analysis_date} for backtesting purposes.*"

            else:
                # Current analysis (existing behavior)
                print(f"Performing current analysis for {ticker}")
                result = self.api_wrapper.analyze_financial_statements(ticker)
                return format_financial_analysis(result)

        except Exception as e:
            import traceback
            print(f"Error in financial analysis: {repr(e)}")
            print(traceback.format_exc())
            return f"Error analyzing financial statements: {repr(e)}"