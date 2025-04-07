"""Util that calls Alpha Vantage API."""

import json
import time
from typing import Dict, List, Optional
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
        api_key = get_from_dict_or_env(
            values, "api_key", "ALPHA_VANTAGE_API_KEY"
        )
        values["api_key"] = api_key
        return values

    def _get_cached_or_fetch(self, endpoint: str, func, *args, **kwargs) -> Dict:
        """Get data from cache or fetch from API."""
        cache_key = endpoint
        current_time = time.time()

        # Return from cache if available and not expired
        if cache_key in self.cache and current_time - self.cache_timestamp.get(cache_key, 0) < self.base_cache_time:
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
                **kwargs
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
        result = {
            "ticker": ticker,
            "timestamp": time.time()
        }

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
                result["balance_sheet_error"] = balance_sheet.get("error", "Unknown error")
        except Exception as e:
            result["balance_sheet_error"] = str(e)

        # Income statement data
        try:
            income_statement = self.get_income_statement(ticker)
            if "error" not in income_statement:
                result["income_statement"] = income_statement
            else:
                result["income_statement_error"] = income_statement.get("error", "Unknown error")
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
                    analysis["market_cap"] = f"${float(profile['MarketCapitalization']):,.2f}"
                if "FullTimeEmployees" in profile:
                    analysis["employees"] = f"{profile['FullTimeEmployees']}"

                # Basic financials from overview
                if "EPS" in profile:
                    analysis["eps"] = f"${float(profile['EPS']):,.2f}"
                if "PERatio" in profile:
                    analysis["pe_ratio"] = f"{float(profile['PERatio']):,.2f}"
                if "PEGRatio" in profile:
                    analysis["peg_ratio"] = f"{float(profile['PEGRatio']):,.2f}"
                if "DividendYield" in profile:
                    analysis["dividend_yield"] = f"{float(profile['DividendYield']) * 100:,.2f}%"
                if "PriceToBookRatio" in profile:
                    analysis["pb_ratio"] = f"{float(profile['PriceToBookRatio']):,.2f}"
                if "ReturnOnEquityTTM" in profile:
                    roe = float(profile['ReturnOnEquityTTM']) * 100
                    analysis["roe"] = f"{roe:,.2f}%"
                    if roe > 15:
                        analysis["roe_evaluation"] = "Excellent ROE"
                    elif roe > 10:
                        analysis["roe_evaluation"] = "Good ROE"
                    elif roe > 5:
                        analysis["roe_evaluation"] = "Average ROE"
                    else:
                        analysis["roe_evaluation"] = "Below average ROE"
                if "ReturnOnAssetsTTM" in profile:
                    analysis["roa"] = f"{float(profile['ReturnOnAssetsTTM']) * 100:,.2f}%"
                if "OperatingMarginTTM" in profile:
                    op_margin = float(profile['OperatingMarginTTM']) * 100
                    analysis["operating_margin"] = f"{op_margin:,.2f}%"
                    if op_margin > 15:
                        analysis["profitability_evaluation"] = "Excellent profitability"
                    elif op_margin > 10:
                        analysis["profitability_evaluation"] = "Good profitability"
                    elif op_margin > 5:
                        analysis["profitability_evaluation"] = "Average profitability"
                    else:
                        analysis["profitability_evaluation"] = "Below average profitability"
                if "ProfitMargin" in profile:
                    analysis["profit_margin"] = f"{float(profile['ProfitMargin']) * 100:,.2f}%"
            except Exception as e:
                analysis["profile_analysis_error"] = str(e)

        # Balance sheet analysis
        balance_sheet_data = data.get("balance_sheet", {})
        if balance_sheet_data and "annualReports" in balance_sheet_data and len(balance_sheet_data["annualReports"]) > 0:
            try:
                recent = balance_sheet_data["annualReports"][0]

                # Extract basic metrics
                total_assets = float(recent.get("totalAssets", 0))
                total_liabilities = float(recent.get("totalLiabilities", 0))
                total_equity = float(recent.get("totalShareholderEquity", 0))

                # Add basic metrics
                analysis["total_assets"] = f"${total_assets:,.2f}"
                analysis["total_liabilities"] = f"${total_liabilities:,.2f}"
                analysis["total_equity"] = f"${total_equity:,.2f}"

                # Liquidity analysis
                current_assets = float(recent.get("totalCurrentAssets", 0))
                current_liabilities = float(recent.get("totalCurrentLiabilities", 0))

                analysis["current_assets"] = f"${current_assets:,.2f}"
                analysis["current_liabilities"] = f"${current_liabilities:,.2f}"

                if current_liabilities > 0:
                    current_ratio = (current_assets / current_liabilities)
                    analysis["current_ratio"] = f"{current_ratio:.2f}"

                    if current_ratio > 2:
                        analysis["liquidity_evaluation"] = "Excellent liquidity"
                    elif current_ratio > 1.5:
                        analysis["liquidity_evaluation"] = "Good liquidity"
                    elif current_ratio > 1:
                        analysis["liquidity_evaluation"] = "Adequate liquidity"
                    else:
                        analysis["liquidity_evaluation"] = "Potential liquidity risk"

                # Debt ratio
                if total_equity > 0:
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
            except Exception as e:
                analysis["balance_sheet_analysis_error"] = str(e)

        # Income statement analysis
        income_statement_data = data.get("income_statement", {})
        if income_statement_data and "annualReports" in income_statement_data and len(income_statement_data["annualReports"]) >= 2:
            try:
                recent = income_statement_data["annualReports"][0]
                previous = income_statement_data["annualReports"][1]

                # Extract metrics
                recent_revenue = float(recent.get("totalRevenue", 0))
                recent_gross_profit = float(recent.get("grossProfit", 0))
                recent_operating_income = float(recent.get("operatingIncome", 0))
                recent_net_income = float(recent.get("netIncome", 0))

                previous_revenue = float(previous.get("totalRevenue", 0))
                previous_net_income = float(previous.get("netIncome", 0))

                # Add basic metrics
                analysis["recent_revenue"] = f"${recent_revenue:,.2f}"
                analysis["recent_gross_profit"] = f"${recent_gross_profit:,.2f}"
                analysis["recent_operating_income"] = f"${recent_operating_income:,.2f}"
                analysis["recent_net_income"] = f"${recent_net_income:,.2f}"

                # Growth rates
                if previous_revenue > 0:
                    revenue_growth = ((recent_revenue - previous_revenue) / previous_revenue) * 100
                    analysis["revenue_growth"] = f"{revenue_growth:.2f}%"

                    if revenue_growth > 20:
                        analysis["revenue_growth_evaluation"] = "Strong revenue growth"
                    elif revenue_growth > 5:
                        analysis["revenue_growth_evaluation"] = "Good revenue growth"
                    elif revenue_growth > 0:
                        analysis["revenue_growth_evaluation"] = "Modest revenue growth"
                    else:
                        analysis["revenue_growth_evaluation"] = "Declining revenue"

                # Profitability
                if recent_revenue > 0:
                    gross_margin = (recent_gross_profit / recent_revenue) * 100
                    operating_margin = (recent_operating_income / recent_revenue) * 100
                    net_margin = (recent_net_income / recent_revenue) * 100

                    analysis["gross_margin"] = f"{gross_margin:.2f}%"
                    if "operating_margin" not in analysis:  # Only add if not already added from profile
                        analysis["operating_margin"] = f"{operating_margin:.2f}%"
                        if operating_margin > 15:
                            analysis["profitability_evaluation"] = "Excellent profitability"
                        elif operating_margin > 10:
                            analysis["profitability_evaluation"] = "Good profitability"
                        elif operating_margin > 5:
                            analysis["profitability_evaluation"] = "Average profitability"
                        else:
                            analysis["profitability_evaluation"] = "Below average profitability"
                    analysis["net_margin"] = f"{net_margin:.2f}%"

                # Net income growth
                if previous_net_income > 0:
                    net_income_growth = ((recent_net_income - previous_net_income) / previous_net_income) * 100
                    analysis["net_income_growth"] = f"{net_income_growth:.2f}%"
            except Exception as e:
                analysis["income_statement_analysis_error"] = str(e)

        return analysis