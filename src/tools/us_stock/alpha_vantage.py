"""Util that calls Alpha Vantage API."""

import time
from typing import Dict, Optional, Any
import requests

from langchain_core.utils import get_from_dict_or_env
from pydantic import BaseModel, ConfigDict, SecretStr, model_validator


class AlphaVantageAPIWrapper(BaseModel):
    """Wrapper for Alpha Vantage API."""

    api_key: SecretStr
    base_url: str = "https://www.alphavantage.co/query"
    cache: Dict = {}
    cache_timestamp: Dict = {}
    base_cache_time: int = 86400  # Cache time in seconds (1 day)

    model_config = ConfigDict(
        extra="forbid",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key exists in environment."""
        api_key = get_from_dict_or_env(values, "api_key", "ALPHA_VANTAGE_API_KEY")
        values["api_key"] = api_key
        return values

    def safe_float_or_empty(self, value: Any) -> Optional[float]:
        """
        Convert string value to float.
        Return None when conversion is not possible.
        """
        if (
            value is None
            or value == "None"
            or value == ""
            or (isinstance(value, str) and value.strip().lower() == "none")
        ):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def format_financial_value(
        self, value: Any, include_dollar: bool = True, include_percent: bool = False
    ) -> str:
        """
        Format financial values.
        Return 'No data' for None values.
        """
        if value is None:
            return "No data"

        try:
            float_value = self.safe_float_or_empty(value)
            if float_value is None:
                return "No data"

            if include_percent:
                return f"{float_value * 100:.2f}%"
            elif include_dollar:
                return f"${float_value:,.2f}"
            else:
                return f"{float_value:,.2f}"
        except (ValueError, TypeError):
            return "No data"

    def _get_cached_or_fetch(self, endpoint: str, func, *args, **kwargs) -> Dict:
        """Get data from cache or fetch from API."""
        cache_key = endpoint
        current_time = time.time()

        # Return from cache if available and not expired
        if (
            cache_key in self.cache
            and current_time - self.cache_timestamp.get(cache_key, 0)
            < self.base_cache_time
        ):
            return self.cache[cache_key]

        # Fetch new data
        result = func(*args, **kwargs)

        # Cache the result
        self.cache[cache_key] = result
        self.cache_timestamp[cache_key] = current_time

        return result

    def make_request(self, function: str, symbol: str, **kwargs) -> Dict:
        """Make API request to Alpha Vantage."""
        try:
            params = {
                "function": function,
                "symbol": symbol,
                "apikey": self.api_key.get_secret_value(),
                **kwargs,
            }

            response = requests.get(self.base_url, params=params)

            if response.status_code != 200:
                return {"error": f"API request failed: {response.text}"}

            data = response.json()

            # Check for error messages in the response
            if "Error Message" in data:
                return {"error": data["Error Message"]}

            if "Note" in data and "API call frequency" in data["Note"]:
                return {"error": f"API call frequency exceeded: {data['Note']}"}

            return data
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

    def get_company_overview(self, ticker: str) -> Dict:
        """Get company overview."""
        cache_key = f"overview_{ticker}"

        def fetch_overview():
            return self.make_request("OVERVIEW", ticker)

        return self._get_cached_or_fetch(cache_key, fetch_overview)

    def get_balance_sheet(self, ticker: str) -> Dict:
        """Get balance sheet statement."""
        cache_key = f"balance_sheet_{ticker}"

        def fetch_balance_sheet():
            return self.make_request("BALANCE_SHEET", ticker)

        return self._get_cached_or_fetch(cache_key, fetch_balance_sheet)

    def get_income_statement(self, ticker: str) -> Dict:
        """Get income statement."""
        cache_key = f"income_statement_{ticker}"

        def fetch_income_statement():
            return self.make_request("INCOME_STATEMENT", ticker)

        return self._get_cached_or_fetch(cache_key, fetch_income_statement)

    def get_cash_flow(self, ticker: str) -> Dict:
        """Get cash flow statement."""
        cache_key = f"cash_flow_{ticker}"

        def fetch_cash_flow():
            return self.make_request("CASH_FLOW", ticker)

        return self._get_cached_or_fetch(cache_key, fetch_cash_flow)

    def get_earnings(self, ticker: str) -> Dict:
        """Get quarterly and annual earnings."""
        cache_key = f"earnings_{ticker}"

        def fetch_earnings():
            return self.make_request("EARNINGS", ticker)

        return self._get_cached_or_fetch(cache_key, fetch_earnings)

    def get_time_series_daily(self, ticker: str, outputsize: str = "compact") -> Dict:
        """Get daily time series of stock prices."""
        cache_key = f"time_series_daily_{ticker}_{outputsize}"

        def fetch_time_series():
            return self.make_request("TIME_SERIES_DAILY", ticker, outputsize=outputsize)

        return self._get_cached_or_fetch(cache_key, fetch_time_series)

    def get_sector_performance(self) -> Dict:
        """Get sector performance data."""
        cache_key = "sector_performance"

        def fetch_sector_performance():
            return self.make_request("SECTOR", "")

        return self._get_cached_or_fetch(cache_key, fetch_sector_performance)

    def analyze_financial_statements(self, ticker: str) -> Dict:
        """Analyze financial statements for a stock."""
        result = {"ticker": ticker, "timestamp": time.time()}

        # Get company overview
        try:
            overview = self.get_company_overview(ticker)
            if "error" not in overview:
                result["profile"] = overview
                result["company_name"] = overview.get("Name", "")
            else:
                result["profile_error"] = overview.get("error", "Unknown error")
        except Exception as e:
            result["profile_error"] = str(e)

        # Balance sheet data
        try:
            balance_sheet = self.get_balance_sheet(ticker)
            if "error" not in balance_sheet:
                result["balance_sheet"] = balance_sheet
            else:
                result["balance_sheet_error"] = balance_sheet.get(
                    "error", "Unknown error"
                )
        except Exception as e:
            result["balance_sheet_error"] = str(e)

        # Income statement data
        try:
            income_statement = self.get_income_statement(ticker)
            if "error" not in income_statement:
                result["income_statement"] = income_statement
            else:
                result["income_statement_error"] = income_statement.get(
                    "error", "Unknown error"
                )
        except Exception as e:
            result["income_statement_error"] = str(e)

        # Cash flow data
        try:
            cash_flow = self.get_cash_flow(ticker)
            if "error" not in cash_flow:
                result["cash_flow"] = cash_flow
            else:
                result["cash_flow_error"] = cash_flow.get("error", "Unknown error")
        except Exception as e:
            result["cash_flow_error"] = str(e)

        # Add analysis results
        result["analysis"] = self._analyze_financial_data(result)

        return result

    def _analyze_financial_data(self, data: Dict) -> Dict:
        """Analyze financial statement data."""
        analysis = {}

        # Profile analysis
        profile = data.get("profile", {})
        if profile:
            try:
                # Extract key profile details
                if "Sector" in profile:
                    analysis["sector"] = profile["Sector"]
                if "Industry" in profile:
                    analysis["industry"] = profile["Industry"]
                if "MarketCapitalization" in profile:
                    market_cap = self.safe_float_or_empty(
                        profile["MarketCapitalization"]
                    )
                    analysis["market_cap"] = self.format_financial_value(market_cap)
                if "FullTimeEmployees" in profile:
                    analysis["employees"] = (
                        profile["FullTimeEmployees"]
                        if profile["FullTimeEmployees"]
                        else "No data"
                    )

                # Basic financials from overview
                if "EPS" in profile:
                    eps = self.safe_float_or_empty(profile["EPS"])
                    analysis["eps"] = self.format_financial_value(eps)
                if "PERatio" in profile:
                    pe_ratio = self.safe_float_or_empty(profile["PERatio"])
                    analysis["pe_ratio"] = self.format_financial_value(
                        pe_ratio, include_dollar=False
                    )
                if "PEGRatio" in profile:
                    peg_ratio = self.safe_float_or_empty(profile["PEGRatio"])
                    analysis["peg_ratio"] = self.format_financial_value(
                        peg_ratio, include_dollar=False
                    )
                if "DividendYield" in profile:
                    div_yield = self.safe_float_or_empty(profile["DividendYield"])
                    if div_yield is not None:
                        analysis["dividend_yield"] = self.format_financial_value(
                            div_yield * 100, include_dollar=False, include_percent=True
                        )
                    else:
                        analysis["dividend_yield"] = "No data"
                if "PriceToBookRatio" in profile:
                    pb_ratio = self.safe_float_or_empty(profile["PriceToBookRatio"])
                    analysis["pb_ratio"] = self.format_financial_value(
                        pb_ratio, include_dollar=False
                    )
                if "ReturnOnEquityTTM" in profile:
                    roe = self.safe_float_or_empty(profile["ReturnOnEquityTTM"])
                    if roe is not None:
                        roe_value = roe * 100
                        analysis["roe"] = self.format_financial_value(
                            roe_value, include_dollar=False, include_percent=True
                        )
                        if roe_value > 15:
                            analysis["roe_evaluation"] = "Excellent ROE"
                        elif roe_value > 10:
                            analysis["roe_evaluation"] = "Good ROE"
                        elif roe_value > 5:
                            analysis["roe_evaluation"] = "Average ROE"
                        else:
                            analysis["roe_evaluation"] = "Below average ROE"
                    else:
                        analysis["roe"] = "No data"
                        analysis["roe_evaluation"] = (
                            "Unable to evaluate due to insufficient data"
                        )
                if "ReturnOnAssetsTTM" in profile:
                    roa = self.safe_float_or_empty(profile["ReturnOnAssetsTTM"])
                    if roa is not None:
                        analysis["roa"] = self.format_financial_value(
                            roa * 100, include_dollar=False, include_percent=True
                        )
                    else:
                        analysis["roa"] = "No data"
                if "OperatingMarginTTM" in profile:
                    op_margin = self.safe_float_or_empty(profile["OperatingMarginTTM"])
                    if op_margin is not None:
                        op_margin_value = op_margin * 100
                        analysis["operating_margin"] = self.format_financial_value(
                            op_margin_value, include_dollar=False, include_percent=True
                        )
                        if op_margin_value > 15:
                            analysis["profitability_evaluation"] = (
                                "Excellent profitability"
                            )
                        elif op_margin_value > 10:
                            analysis["profitability_evaluation"] = "Good profitability"
                        elif op_margin_value > 5:
                            analysis["profitability_evaluation"] = (
                                "Average profitability"
                            )
                        else:
                            analysis["profitability_evaluation"] = (
                                "Below average profitability"
                            )
                    else:
                        analysis["operating_margin"] = "No data"
                        analysis["profitability_evaluation"] = (
                            "Unable to evaluate due to insufficient data"
                        )
                if "ProfitMargin" in profile:
                    profit_margin = self.safe_float_or_empty(profile["ProfitMargin"])
                    if profit_margin is not None:
                        analysis["profit_margin"] = self.format_financial_value(
                            profit_margin * 100,
                            include_dollar=False,
                            include_percent=True,
                        )
                    else:
                        analysis["profit_margin"] = "No data"
            except Exception as e:
                analysis["profile_analysis_error"] = str(e)

        # Balance sheet analysis
        balance_sheet_data = data.get("balance_sheet", {})
        if (
            balance_sheet_data
            and "annualReports" in balance_sheet_data
            and len(balance_sheet_data["annualReports"]) > 0
        ):
            try:
                recent = balance_sheet_data["annualReports"][0]

                # Extract basic metrics - safely convert values
                total_assets = self.safe_float_or_empty(recent.get("totalAssets"))
                total_liabilities = self.safe_float_or_empty(
                    recent.get("totalLiabilities")
                )
                total_equity = self.safe_float_or_empty(
                    recent.get("totalShareholderEquity")
                )

                # Add basic metrics
                analysis["total_assets"] = self.format_financial_value(total_assets)
                analysis["total_liabilities"] = self.format_financial_value(
                    total_liabilities
                )
                analysis["total_equity"] = self.format_financial_value(total_equity)

                # Liquidity analysis
                current_assets = self.safe_float_or_empty(
                    recent.get("totalCurrentAssets")
                )
                current_liabilities = self.safe_float_or_empty(
                    recent.get("totalCurrentLiabilities")
                )

                analysis["current_assets"] = self.format_financial_value(current_assets)
                analysis["current_liabilities"] = self.format_financial_value(
                    current_liabilities
                )

                if (
                    current_liabilities is not None
                    and current_assets is not None
                    and current_liabilities > 0
                ):
                    current_ratio = current_assets / current_liabilities
                    analysis["current_ratio"] = f"{current_ratio:.2f}"

                    if current_ratio > 2:
                        analysis["liquidity_evaluation"] = "Excellent liquidity"
                    elif current_ratio > 1.5:
                        analysis["liquidity_evaluation"] = "Good liquidity"
                    elif current_ratio > 1:
                        analysis["liquidity_evaluation"] = "Adequate liquidity"
                    else:
                        analysis["liquidity_evaluation"] = "Potential liquidity risk"
                else:
                    analysis["current_ratio"] = "No data"
                    analysis["liquidity_evaluation"] = (
                        "Unable to evaluate due to insufficient data"
                    )

                # Debt ratio
                if (
                    total_equity is not None
                    and total_liabilities is not None
                    and total_equity > 0
                ):
                    debt_to_equity = (total_liabilities / total_equity) * 100
                    analysis["debt_to_equity"] = f"{debt_to_equity:.2f}%"

                    if debt_to_equity < 50:
                        analysis["debt_evaluation"] = "Very low debt (conservative)"
                    elif debt_to_equity < 100:
                        analysis["debt_evaluation"] = "Moderate debt"
                    elif debt_to_equity < 200:
                        analysis["debt_evaluation"] = "High debt (aggressive)"
                    else:
                        analysis["debt_evaluation"] = "Very high debt (risky)"
                else:
                    analysis["debt_to_equity"] = "No data"
                    analysis["debt_evaluation"] = (
                        "Unable to evaluate due to insufficient data"
                    )
            except Exception as e:
                analysis["balance_sheet_analysis_error"] = str(e)

        # Income statement analysis
        income_statement_data = data.get("income_statement", {})
        if (
            income_statement_data
            and "annualReports" in income_statement_data
            and len(income_statement_data["annualReports"]) >= 2
        ):
            try:
                recent = income_statement_data["annualReports"][0]
                previous = income_statement_data["annualReports"][1]

                # Extract metrics - safely convert values
                recent_revenue = self.safe_float_or_empty(recent.get("totalRevenue"))
                recent_gross_profit = self.safe_float_or_empty(
                    recent.get("grossProfit")
                )
                recent_operating_income = self.safe_float_or_empty(
                    recent.get("operatingIncome")
                )
                recent_net_income = self.safe_float_or_empty(recent.get("netIncome"))

                previous_revenue = self.safe_float_or_empty(
                    previous.get("totalRevenue")
                )
                previous_net_income = self.safe_float_or_empty(
                    previous.get("netIncome")
                )

                # Add basic metrics
                analysis["recent_revenue"] = self.format_financial_value(recent_revenue)
                analysis["recent_gross_profit"] = self.format_financial_value(
                    recent_gross_profit
                )
                analysis["recent_operating_income"] = self.format_financial_value(
                    recent_operating_income
                )
                analysis["recent_net_income"] = self.format_financial_value(
                    recent_net_income
                )

                # Growth rates - calculate only if data is available
                if (
                    previous_revenue is not None
                    and recent_revenue is not None
                    and previous_revenue > 0
                ):
                    revenue_growth = (
                        (recent_revenue - previous_revenue) / previous_revenue
                    ) * 100
                    analysis["revenue_growth"] = f"{revenue_growth:.2f}%"

                    if revenue_growth > 20:
                        analysis["revenue_growth_evaluation"] = "Strong revenue growth"
                    elif revenue_growth > 5:
                        analysis["revenue_growth_evaluation"] = "Good revenue growth"
                    elif revenue_growth > 0:
                        analysis["revenue_growth_evaluation"] = "Modest revenue growth"
                    else:
                        analysis["revenue_growth_evaluation"] = "Declining revenue"
                else:
                    analysis["revenue_growth"] = "No data"
                    analysis["revenue_growth_evaluation"] = (
                        "Unable to evaluate due to insufficient data"
                    )

                # Profitability - calculate only if data is available
                if recent_revenue is not None and recent_revenue > 0:
                    if recent_gross_profit is not None:
                        gross_margin = (recent_gross_profit / recent_revenue) * 100
                        analysis["gross_margin"] = f"{gross_margin:.2f}%"
                    else:
                        analysis["gross_margin"] = "No data"

                    if recent_operating_income is not None:
                        operating_margin = (
                            recent_operating_income / recent_revenue
                        ) * 100
                        if (
                            "operating_margin" not in analysis
                        ):  # Only add if not already added from profile
                            analysis["operating_margin"] = f"{operating_margin:.2f}%"
                            if operating_margin > 15:
                                analysis["profitability_evaluation"] = (
                                    "Excellent profitability"
                                )
                            elif operating_margin > 10:
                                analysis["profitability_evaluation"] = (
                                    "Good profitability"
                                )
                            elif operating_margin > 5:
                                analysis["profitability_evaluation"] = (
                                    "Average profitability"
                                )
                            else:
                                analysis["profitability_evaluation"] = (
                                    "Below average profitability"
                                )
                    else:
                        if "operating_margin" not in analysis:
                            analysis["operating_margin"] = "No data"
                            analysis["profitability_evaluation"] = (
                                "Unable to evaluate due to insufficient data"
                            )

                    if recent_net_income is not None:
                        net_margin = (recent_net_income / recent_revenue) * 100
                        analysis["net_margin"] = f"{net_margin:.2f}%"
                    else:
                        analysis["net_margin"] = "No data"
                else:
                    analysis["gross_margin"] = "No data"
                    if "operating_margin" not in analysis:
                        analysis["operating_margin"] = "No data"
                        analysis["profitability_evaluation"] = (
                            "Unable to evaluate due to insufficient data"
                        )
                    analysis["net_margin"] = "No data"

                # Net income growth - calculate only if data is available
                if (
                    previous_net_income is not None
                    and recent_net_income is not None
                    and previous_net_income > 0
                ):
                    net_income_growth = (
                        (recent_net_income - previous_net_income) / previous_net_income
                    ) * 100
                    analysis["net_income_growth"] = f"{net_income_growth:.2f}%"
                else:
                    analysis["net_income_growth"] = "No data"
            except Exception as e:
                analysis["income_statement_analysis_error"] = str(e)

        return analysis
