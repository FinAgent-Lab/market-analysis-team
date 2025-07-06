"""Util that calls Alpha Vantage API."""

import time
import logging
from typing import Dict, Optional, Any
import requests

from langchain_core.utils import get_from_dict_or_env
from pydantic import BaseModel, ConfigDict, SecretStr, model_validator


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

            # include_percent=True일 경우 100을 곱하지 않음
            if include_percent:
                return f"{float_value:.2f}%"
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

    def log_raw_financial_metrics(self, profile: Dict) -> None:
        """Log raw financial metrics for debugging."""
        if not profile:
            logger.info("No profile data available to log")
            return

        # Log important financial ratios
        metrics_to_log = [
            "ReturnOnEquityTTM",
            "ReturnOnAssetsTTM",
            "OperatingMarginTTM",
            "ProfitMargin",
            "QuarterlyEarningsGrowthYOY",
            "QuarterlyRevenueGrowthYOY",
            "DividendYield",
            "EPS",
            "ProfitMargin",
            "GrossProfitTTM",
        ]

        logger.info("====== RAW FINANCIAL METRICS ======")
        for metric in metrics_to_log:
            if metric in profile:
                raw_value = profile[metric]
                float_value = self.safe_float_or_empty(raw_value)
                logger.info(
                    f"{metric}: Raw Value = {raw_value}, Float Value = {float_value}"
                )

                # For percentage metrics, show what happens if we multiply by 100
                if metric in [
                    "ReturnOnEquityTTM",
                    "ReturnOnAssetsTTM",
                    "OperatingMarginTTM",
                    "ProfitMargin",
                    "DividendYield",
                ]:
                    if float_value is not None:
                        percentage_value = float_value * 100
                        logger.info(
                            f"{metric} as percentage (x100): {percentage_value:.2f}%"
                        )

        # Log all keys in profile for discovery
        logger.info("====== ALL AVAILABLE PROFILE KEYS ======")
        for key in profile.keys():
            logger.info(f"Available key: {key}")

    def analyze_financial_statements(self, ticker: str) -> Dict:
        """Analyze financial statements for a stock."""
        from . import analyze_financial_data

        result = {"ticker": ticker, "timestamp": time.time()}

        # Get company overview
        try:
            overview = self.get_company_overview(ticker)
            if "error" not in overview:
                # Log raw data for debugging
                self.log_raw_financial_metrics(overview)

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
        result["analysis"] = analyze_financial_data(self, result)

        return result
