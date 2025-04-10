"""Tool for the Korea Investment & Securities API financial statements analysis."""

from typing import Dict, Optional, Type, Union

from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.hantoo_stock.hantoo_stock import HantooStockAPIWrapper


class HantooStockInput(BaseModel):
    """Input for the Hantoo financial statement analysis tool."""

    query: str = Field(description="query containing Korean stock code (6 digits)")


class HantooFinancialStatementTool(BaseTool):
    """Tool that analyzes financial statements using Korea Investment & Securities API.

    Setup:
        Set environment variables ``HANTOO_APP_KEY`` and ``HANTOO_APP_SECRET``.

        .. code-block:: bash

            export HANTOO_APP_KEY="your-app-key"
            export HANTOO_APP_SECRET="your-app-secret"

    """

    name: str = "hantoo_financial_statement_analyzer"
    description: str = (
        "A tool for analyzing financial statements of Korean stocks using Korea Investment & Securities API. "
        "Analyzes balance sheets, income statements, and financial ratios. "
        "Input should be a query containing the Korean stock code (6 digits)."
    )
    args_schema: Type[BaseModel] = HantooStockInput
    api_wrapper: HantooStockAPIWrapper = Field(default_factory=HantooStockAPIWrapper)

    def _extract_stock_code(self, query: str) -> Optional[str]:
        """Extract stock code from query."""
        import re

        # Try to find a 6-digit code in the query
        match = re.search(r"(\d{6})", query)
        if match:
            return match.group(1)

        # If no direct code is found, look for patterns like "code: 005930" or "Samsung Electronics(005930)"
        match = re.search(
            r"(?:[code|stock code]?[:\s]*|[^\w\d]*\()(\d{6})(?:\)|)", query
        )
        if match:
            return match.group(1)

        return None

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Union[Dict, str]:
        """Run the tool."""
        try:
            stock_code = self._extract_stock_code(query)
            if not stock_code:
                return "No valid stock code (6 digits) found in the query. Please provide a query with a stock code."

            # Get analysis from the API wrapper
            result = self.api_wrapper.analyze_financial_statements(stock_code)

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

        stock_code = analysis_data.get("stock_code", "Unknown")
        output.append(f"# Financial Statement Analysis for Stock Code {stock_code}")

        # Balance sheet information
        balance_sheet = analysis_data.get("balance_sheet", [])
        if balance_sheet and len(balance_sheet) > 0:
            output.append("\n## Balance Sheet Information")
            recent = balance_sheet[0]
            period = recent.get("stac_yymm", "N/A")
            output.append(f"Reference Period: {period}")

            if "total_aset" in recent:
                output.append(f"- Total Assets: {recent['total_aset']} million KRW")
            if "cras" in recent:
                output.append(f"- Current Assets: {recent['cras']} million KRW")
            if "fxas" in recent:
                output.append(f"- Fixed Assets: {recent['fxas']} million KRW")
            if "total_lblt" in recent:
                output.append(
                    f"- Total Liabilities: {recent['total_lblt']} million KRW"
                )
            if "flow_lblt" in recent:
                output.append(
                    f"- Current Liabilities: {recent['flow_lblt']} million KRW"
                )
            if "total_cptl" in recent:
                output.append(f"- Total Equity: {recent['total_cptl']} million KRW")

        # Income statement information
        income_statement = analysis_data.get("income_statement", [])
        if income_statement and len(income_statement) > 0:
            output.append("\n## Income Statement Information")
            recent = income_statement[0]
            period = recent.get("stac_yymm", "N/A")
            output.append(f"Reference Period: {period}")

            if "sale_account" in recent:
                output.append(f"- Revenue: {recent['sale_account']} million KRW")
            if "sale_cost" in recent:
                output.append(
                    f"- Cost of Goods Sold: {recent['sale_cost']} million KRW"
                )
            if "sale_totl_prfi" in recent:
                output.append(f"- Gross Profit: {recent['sale_totl_prfi']} million KRW")
            if "bsop_prti" in recent:
                output.append(f"- Operating Profit: {recent['bsop_prti']} million KRW")
            if "thtr_ntin" in recent:
                output.append(f"- Net Income: {recent['thtr_ntin']} million KRW")

        # Financial ratios information
        financial_ratios = analysis_data.get("financial_ratios", [])
        if financial_ratios and len(financial_ratios) > 0:
            output.append("\n## Financial Ratios")
            recent = financial_ratios[0]
            period = recent.get("stac_yymm", "N/A")
            output.append(f"Reference Period: {period}")

            if "roe_val" in recent:
                output.append(f"- ROE (Return on Equity): {recent['roe_val']}%")
            if "eps" in recent:
                output.append(f"- EPS (Earnings Per Share): {recent['eps']} KRW")
            if "bps" in recent:
                output.append(f"- BPS (Book Value Per Share): {recent['bps']} KRW")
            if "rsrv_rate" in recent:
                output.append(f"- Retention Rate: {recent['rsrv_rate']}%")
            if "lblt_rate" in recent:
                output.append(f"- Debt Ratio: {recent['lblt_rate']}%")

        # Analysis information
        analysis = analysis_data.get("analysis", {})
        if analysis:
            output.append("\n## Financial Analysis")

            # Liquidity analysis
            if "current_ratio" in analysis:
                output.append(f"- Current Ratio: {analysis['current_ratio']}")
                if "liquidity_evaluation" in analysis:
                    output.append(f"  - Evaluation: {analysis['liquidity_evaluation']}")

            # Debt analysis
            if "debt_ratio" in analysis:
                output.append(f"- Debt Ratio: {analysis['debt_ratio']}")
                if "debt_evaluation" in analysis:
                    output.append(f"  - Evaluation: {analysis['debt_evaluation']}")

            # Growth analysis
            if "sales_growth" in analysis:
                output.append(f"- Sales Growth: {analysis['sales_growth']}")
                if "sales_growth_evaluation" in analysis:
                    output.append(
                        f"  - Evaluation: {analysis['sales_growth_evaluation']}"
                    )

            # Profitability analysis
            if "operating_margin" in analysis:
                output.append(f"- Operating Margin: {analysis['operating_margin']}")
                if "profitability_evaluation" in analysis:
                    output.append(
                        f"  - Evaluation: {analysis['profitability_evaluation']}"
                    )

            # ROE analysis
            if "roe" in analysis:
                output.append(f"- ROE: {analysis['roe']}")
                if "roe_evaluation" in analysis:
                    output.append(f"  - Evaluation: {analysis['roe_evaluation']}")

            # Net income growth
            if "net_income_growth" in analysis:
                output.append(f"- Net Income Growth: {analysis['net_income_growth']}")

        return "\n".join(output)
