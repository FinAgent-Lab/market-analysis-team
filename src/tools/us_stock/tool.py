"""Tool for the Alpha Vantage financial statements analysis."""

from typing import Dict, List, Optional, Type, Union, Any
from typing_extensions import Literal

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, root_validator

from src.tools.us_stock.alpha_vantage import AlphaVantageAPIWrapper


class USStockInput(BaseModel):
    """Input for the US financial statement analysis tool."""
    query: str = Field(description="query containing company name or US stock ticker symbol (e.g., Apple, AAPL, Microsoft, MSFT)")


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

    # llm 속성을 private로 설정하여 Pydantic 검증에서 제외
    _llm = None

    @property
    def llm(self):
        return self._llm

    @llm.setter
    def llm(self, value):
        self._llm = value

    def _extract_ticker(self, query: str) -> Optional[str]:
        """Extract ticker from query using LLM inference and validate with Alpha Vantage API."""
        # LLM이 없으면 None 반환
        if self.llm is None:
            return None

        # LLM에게 회사 이름을 티커로 변환하도록 요청
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
            # LLM에 질의
            response = self.llm.predict(prompt).strip().upper()

            # 응답이 유효한 티커 형식인지 확인 (1-5개의 대문자)
            import re
            if response != "UNKNOWN" and re.match(r'^[A-Z]{1,5}$', response):
                # Alpha Vantage API를 통해 실제 존재하는지 확인
                try:
                    result = self.api_wrapper.get_company_overview(response)
                    if "error" not in result:
                        return response
                except Exception as e:
                    print(f"Error verifying ticker with Alpha Vantage: {e}")
                    # API 검증에 실패해도 일단 티커 형식이 맞으면 반환 (선택적)
                    # return response

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
            if "Sector" in profile:
                output.append(f"- Sector: {profile['Sector']}")
            if "Industry" in profile:
                output.append(f"- Industry: {profile['Industry']}")
            if "Description" in profile:
                output.append(f"- Description: {profile['Description'][:300]}...")
            if "MarketCapitalization" in profile:
                output.append(f"- Market Cap: ${float(profile['MarketCapitalization']):,.2f}")
            if "FullTimeEmployees" in profile and profile['FullTimeEmployees']:
                output.append(f"- Employees: {profile['FullTimeEmployees']}")
            if "DividendYield" in profile and profile['DividendYield']:
                output.append(f"- Dividend Yield: {float(profile['DividendYield']) * 100:.2f}%")
            if "52WeekHigh" in profile and "52WeekLow" in profile:
                output.append(f"- 52-Week Range: ${float(profile['52WeekLow']):.2f} - ${float(profile['52WeekHigh']):.2f}")

        # Balance sheet information
        balance_sheet = analysis_data.get("balance_sheet", {}).get("annualReports", [])
        if balance_sheet and len(balance_sheet) > 0:
            output.append("\n## Balance Sheet Information")
            recent = balance_sheet[0]
            period = recent.get("fiscalDateEnding", "N/A")
            output.append(f"Reference Period: {period}")

            if "totalAssets" in recent:
                output.append(f"- Total Assets: ${float(recent['totalAssets']):,.2f}")
            if "totalCurrentAssets" in recent:
                output.append(f"- Current Assets: ${float(recent['totalCurrentAssets']):,.2f}")
            if "totalLiabilities" in recent:
                output.append(f"- Total Liabilities: ${float(recent['totalLiabilities']):,.2f}")
            if "totalCurrentLiabilities" in recent:
                output.append(f"- Current Liabilities: ${float(recent['totalCurrentLiabilities']):,.2f}")
            if "totalShareholderEquity" in recent:
                output.append(f"- Total Shareholder Equity: ${float(recent['totalShareholderEquity']):,.2f}")
            if "longTermDebt" in recent:
                output.append(f"- Long-Term Debt: ${float(recent['longTermDebt']):,.2f}")
            if "cash" in recent:
                output.append(f"- Cash and Equivalents: ${float(recent['cash']):,.2f}")

        # Income statement information
        income_statement = analysis_data.get("income_statement", {}).get("annualReports", [])
        if income_statement and len(income_statement) > 0:
            output.append("\n## Income Statement Information")
            recent = income_statement[0]
            period = recent.get("fiscalDateEnding", "N/A")
            output.append(f"Reference Period: {period}")

            if "totalRevenue" in recent:
                output.append(f"- Total Revenue: ${float(recent['totalRevenue']):,.2f}")
            if "costOfRevenue" in recent:
                output.append(f"- Cost of Revenue: ${float(recent['costOfRevenue']):,.2f}")
            if "grossProfit" in recent:
                output.append(f"- Gross Profit: ${float(recent['grossProfit']):,.2f}")
            if "operatingExpenses" in recent:
                output.append(f"- Operating Expenses: ${float(recent['operatingExpenses']):,.2f}")
            if "operatingIncome" in recent:
                output.append(f"- Operating Income: ${float(recent['operatingIncome']):,.2f}")
            if "netIncome" in recent:
                output.append(f"- Net Income: ${float(recent['netIncome']):,.2f}")
            if "ebitda" in recent:
                output.append(f"- EBITDA: ${float(recent['ebitda']):,.2f}")

        # Cash flow information
        cash_flow = analysis_data.get("cash_flow", {}).get("annualReports", [])
        if cash_flow and len(cash_flow) > 0:
            output.append("\n## Cash Flow Information")
            recent = cash_flow[0]
            period = recent.get("fiscalDateEnding", "N/A")
            output.append(f"Reference Period: {period}")

            if "operatingCashflow" in recent:
                output.append(f"- Operating Cash Flow: ${float(recent['operatingCashflow']):,.2f}")
            if "cashflowFromInvestment" in recent:
                output.append(f"- Cash Flow from Investment: ${float(recent['cashflowFromInvestment']):,.2f}")
            if "cashflowFromFinancing" in recent:
                output.append(f"- Cash Flow from Financing: ${float(recent['cashflowFromFinancing']):,.2f}")
            if "capitalExpenditures" in recent:
                output.append(f"- Capital Expenditures: ${float(recent['capitalExpenditures']):,.2f}")
            if "dividendPayout" in recent and float(recent['dividendPayout']) > 0:
                output.append(f"- Dividend Payout: ${float(recent['dividendPayout']):,.2f}")

        # Financial ratios from profile
        if profile:
            output.append("\n## Financial Ratios")

            if "PERatio" in profile:
                output.append(f"- P/E Ratio: {float(profile['PERatio']):,.2f}")
            if "PEGRatio" in profile:
                output.append(f"- PEG Ratio: {float(profile['PEGRatio']):,.2f}")
            if "PriceToBookRatio" in profile:
                output.append(f"- Price to Book Ratio: {float(profile['PriceToBookRatio']):,.2f}")
            if "EPS" in profile:
                output.append(f"- EPS: ${float(profile['EPS']):,.2f}")
            if "ReturnOnEquityTTM" in profile:
                output.append(f"- Return on Equity (TTM): {float(profile['ReturnOnEquityTTM']) * 100:.2f}%")
            if "ReturnOnAssetsTTM" in profile:
                output.append(f"- Return on Assets (TTM): {float(profile['ReturnOnAssetsTTM']) * 100:.2f}%")
            if "OperatingMarginTTM" in profile:
                output.append(f"- Operating Margin (TTM): {float(profile['OperatingMarginTTM']) * 100:.2f}%")
            if "ProfitMargin" in profile:
                output.append(f"- Profit Margin: {float(profile['ProfitMargin']) * 100:.2f}%")
            if "QuarterlyEarningsGrowthYOY" in profile:
                output.append(f"- Quarterly Earnings Growth (YOY): {float(profile['QuarterlyEarningsGrowthYOY']) * 100:.2f}%")
            if "QuarterlyRevenueGrowthYOY" in profile:
                output.append(f"- Quarterly Revenue Growth (YOY): {float(profile['QuarterlyRevenueGrowthYOY']) * 100:.2f}%")

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
                    output.append(f"  - Evaluation: {analysis['revenue_growth_evaluation']}")

            # Profitability analysis
            if "operating_margin" in analysis:
                output.append(f"- Operating Margin: {analysis['operating_margin']}")
                if "profitability_evaluation" in analysis:
                    output.append(f"  - Evaluation: {analysis['profitability_evaluation']}")

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