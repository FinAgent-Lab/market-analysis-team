"""Tool for the Alpha Vantage financial statements analysis."""

from typing import Dict, Optional, Type, Union, Tuple
from datetime import datetime
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
import re

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
        """LLM 설정 시 깨끗한 LLM으로 재생성"""
        if value is None:
            self._llm = None
            return

        # 바인딩된 LLM이 들어오면 깨끗한 LLM으로 재생성
        try:
            # 원본 LLM의 기본 설정만 추출
            original_model = getattr(value, 'model_name', 'gpt-4o-mini')
            original_temperature = getattr(value, 'temperature', 0.2)
            original_base_url = getattr(value, 'openai_api_base', None)
            original_api_key = getattr(value, 'openai_api_key', None)

            # 바인딩된 kwargs에서 유효한 것만 추출
            bound_kwargs = getattr(value, 'kwargs', {})
            clean_model = bound_kwargs.get('model', original_model)
            clean_temperature = bound_kwargs.get('temperature', original_temperature)

            print(f"Creating clean LLM - model: {clean_model}, temperature: {clean_temperature}")

            # 깨끗한 LLM 생성 (query 등의 잘못된 매개변수 제외)
            from langchain_openai import ChatOpenAI
            import os

            clean_llm_params = {
                "model": clean_model,
                "temperature": clean_temperature,
            }

            # API 키 설정
            if original_api_key:
                clean_llm_params["openai_api_key"] = original_api_key
            else:
                clean_llm_params["openai_api_key"] = os.getenv("OPENAI_API_KEY")

            # base_url 설정
            if original_base_url:
                clean_llm_params["base_url"] = original_base_url
            elif os.getenv("OPENAI_BASE_URL"):
                clean_llm_params["base_url"] = os.getenv("OPENAI_BASE_URL")

            # OpenRouter 헤더 (필요한 경우)
            base_url = clean_llm_params.get("base_url", "")
            if "openrouter" in base_url.lower():
                clean_llm_params["default_headers"] = {
                    "HTTP-Referer": os.getenv("HTTP_REFERER", "http://localhost:8000"),
                    "X-Title": os.getenv("X_TITLE", "Market Analysis Team"),
                }

            self._llm = ChatOpenAI(**clean_llm_params)
            print(f"Successfully created clean LLM: {type(self._llm).__name__}")

        except Exception as e:
            print(f"Error creating clean LLM, falling back to default: {e}")
            # 실패 시 기본 LLM 생성
            self._llm = self._create_default_llm()

    def _create_default_llm(self):
        """Create default LLM with strict parameter validation."""
        from langchain_openai import ChatOpenAI
        import os

        clean_params = {
            "model": os.getenv("MAIN_LLM_MODEL", "gpt-4o-mini"),
            "temperature": 0.2,
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
        }

        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url and base_url != "https://api.openai.com/v1":
            clean_params["base_url"] = base_url

        if base_url and "openrouter" in base_url.lower():
            clean_params["default_headers"] = {
                "HTTP-Referer": os.getenv("HTTP_REFERER", "http://localhost:8000"),
                "X-Title": os.getenv("X_TITLE", "Market Analysis Team"),
            }

        return ChatOpenAI(**clean_params)

    def _extract_ticker_and_date(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract both ticker symbol and analysis date from query using LLM only."""
        if self.llm is None:
            print("LLM is not available - creating default LLM")
            self._llm = self._create_default_llm()

        prompt = f"""Extract the ticker symbol and analysis date from this financial query: "{query}"

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

Output only the result in TICKER|DATE format:"""

        try:
            # 디버깅 정보 출력
            print(f"Using LLM: {type(self.llm).__name__}")
            print(f"LLM model: {getattr(self.llm, 'model_name', 'unknown')}")

            # 안전한 LLM 호출
            message = HumanMessage(content=prompt)
            print(f"Calling LLM with message type: {type(message)}")

            response = self.llm.invoke([message])
            print(f"LLM response type: {type(response)}")

            # 응답 내용 추출
            if hasattr(response, "content"):
                result = response.content.strip().upper()
            elif isinstance(response, str):
                result = response.strip().upper()
            else:
                result = str(response).strip().upper()

            print(f"LLM response: {result}")

            # 결과 파싱 및 검증
            if "|" in result:
                ticker, date = result.split("|", 1)

                # 티커 형식 검증 (1-5자 대문자)
                if re.match(r"^[A-Z]{1,5}$", ticker):
                    # 날짜 검증
                    if date == "CURRENT":
                        print(f"Extracted ticker: {ticker}, date: current")
                        return ticker, None
                    else:
                        try:
                            # 날짜 형식 검증
                            datetime.strptime(date, "%Y-%m-%d")
                            print(f"Extracted ticker: {ticker}, date: {date}")
                            return ticker, date
                        except ValueError:
                            print(f"Invalid date format: {date}")
                            # 날짜가 잘못되었더라도 티커는 유효하므로 현재 데이터로 처리
                            return ticker, None
                else:
                    print(f"Invalid ticker format: {ticker}")
                    # LLM이 올바른 형식을 반환하지 못한 경우
                    raise ValueError(f"LLM failed to extract valid ticker from: {query}")
            else:
                print(f"Invalid response format: {result}")
                raise ValueError(f"LLM response format invalid: {result}")

        except Exception as e:
            print(f"Error in LLM ticker extraction: {e}")
            print(f"Exception type: {type(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            # 폴백 없이 에러 발생시키기
            raise ValueError(f"Failed to extract ticker and date using LLM: {str(e)}")

    def _extract_ticker(self, query: str) -> str:
        """Extract ticker symbol (for backward compatibility)."""
        try:
            ticker, _ = self._extract_ticker_and_date(query)
            return ticker or "unknown"
        except Exception as e:
            print(f"Ticker extraction failed: {e}")
            return "unknown"

    def _filter_data_by_date(
            self, data: Dict, target_date: str, report_type: str = "annualReports"
    ) -> Dict:
        """Filter financial data to get the most recent report before or on target date."""
        if "error" in data or report_type not in data:
            return data

        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        reports = data[report_type]

        # Find the most recent report on or before target date
        valid_reports = []
        for report in reports:
            if "fiscalDateEnding" in report:
                try:
                    report_date = datetime.strptime(
                        report["fiscalDateEnding"], "%Y-%m-%d"
                    )
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
            filtered_data["date_filter_warning"] = (
                f"No financial data available as of {target_date}"
            )
            return filtered_data

    def _get_historical_data(self, ticker: str, target_date: str) -> Dict:
        """Get financial data as of a specific date."""
        print(f"Fetching historical data for {ticker} as of {target_date}")

        result = {
            "ticker": ticker,
            "analysis_date": target_date,
            "historical_analysis": True,
        }

        # Get all financial statements
        try:
            balance_sheet = self.api_wrapper.get_balance_sheet(ticker)
            if "error" not in balance_sheet:
                result["balance_sheet"] = self._filter_data_by_date(
                    balance_sheet, target_date, "annualReports"
                )
                # Also get quarterly data if available
                quarterly_bs = self._filter_data_by_date(
                    balance_sheet, target_date, "quarterlyReports"
                )
                if quarterly_bs.get("quarterlyReports"):
                    result["balance_sheet_quarterly"] = quarterly_bs
            else:
                result["balance_sheet_error"] = balance_sheet.get("error")
        except Exception as e:
            result["balance_sheet_error"] = str(e)

        try:
            income_statement = self.api_wrapper.get_income_statement(ticker)
            if "error" not in income_statement:
                result["income_statement"] = self._filter_data_by_date(
                    income_statement, target_date, "annualReports"
                )
                quarterly_is = self._filter_data_by_date(
                    income_statement, target_date, "quarterlyReports"
                )
                if quarterly_is.get("quarterlyReports"):
                    result["income_statement_quarterly"] = quarterly_is
            else:
                result["income_statement_error"] = income_statement.get("error")
        except Exception as e:
            result["income_statement_error"] = str(e)

        try:
            cash_flow = self.api_wrapper.get_cash_flow(ticker)
            if "error" not in cash_flow:
                result["cash_flow"] = self._filter_data_by_date(
                    cash_flow, target_date, "annualReports"
                )
                quarterly_cf = self._filter_data_by_date(
                    cash_flow, target_date, "quarterlyReports"
                )
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
            print(f"Processing query: {query}")

            # Extract ticker and date from query using LLM only
            ticker, analysis_date = self._extract_ticker_and_date(query)

            if not ticker:
                raise ValueError("Failed to extract valid ticker symbol from query")

            print(f"Successfully extracted - Ticker: {ticker}, Date: {analysis_date}")

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
            error_msg = f"Error analyzing financial statements: {str(e)}"
            print(error_msg)
            import traceback
            print(traceback.format_exc())
            return error_msg