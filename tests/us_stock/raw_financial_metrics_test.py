"""Raw financial metrics test for Alpha Vantage API."""

import os
import sys
import unittest
from dotenv import load_dotenv
from src.tools.us_stock.alpha_vantage_client import AlphaVantageAPIWrapper

# Load .env file
load_dotenv()

# Set path
sys.path.append("..")  # Add parent directory


class TestRawFinancialMetrics(unittest.TestCase):
    """Test class for inspecting raw financial metrics"""

    def setUp(self):
        """Test setup"""
        # Check if API key exists in environment variables
        self.api_key_exists = "ALPHA_VANTAGE_API_KEY" in os.environ

        if not self.api_key_exists:
            self.skipTest("API key not configured")

        # Initialize API client
        self.api = AlphaVantageAPIWrapper()

    def test_inspect_raw_financial_metrics_aapl(self):
        """Test raw financial metrics inspection for AAPL"""
        # This test will log raw financial metrics for AAPL
        result = self.api.get_company_overview("AAPL")

        # Log the raw financial metrics
        self.api.log_raw_financial_metrics(result)

        # Basic assertions to make sure the test is meaningful
        self.assertIn("ReturnOnEquityTTM", result)
        self.assertIn("ReturnOnAssetsTTM", result)
        self.assertIn("OperatingMarginTTM", result)

        # Additional outputs for inspection
        print("\n===== Raw Financial Metrics for AAPL =====")
        for key in [
            "ReturnOnEquityTTM",
            "ReturnOnAssetsTTM",
            "OperatingMarginTTM",
            "ProfitMargin",
        ]:
            if key in result:
                print(f"{key}: {result[key]}")
                # Try to convert to float and multiply by 100
                try:
                    value = float(result[key])
                    print(f"{key} as float: {value}")
                    print(f"{key} x 100: {value * 100}")
                except (ValueError, TypeError):
                    print(f"Cannot convert {key} to float")

    def test_inspect_raw_financial_metrics_msft(self):
        """Test raw financial metrics inspection for MSFT"""
        # Test with a different company for comparison
        result = self.api.get_company_overview("MSFT")

        # Log the raw financial metrics
        self.api.log_raw_financial_metrics(result)

        # Basic assertions
        self.assertIn("ReturnOnEquityTTM", result)
        self.assertIn("ReturnOnAssetsTTM", result)

        # Additional outputs for inspection
        print("\n===== Raw Financial Metrics for MSFT =====")
        for key in [
            "ReturnOnEquityTTM",
            "ReturnOnAssetsTTM",
            "OperatingMarginTTM",
            "ProfitMargin",
        ]:
            if key in result:
                print(f"{key}: {result[key]}")
                # Try to convert to float and multiply by 100
                try:
                    value = float(result[key])
                    print(f"{key} as float: {value}")
                    print(f"{key} x 100: {value * 100}")
                except (ValueError, TypeError):
                    print(f"Cannot convert {key} to float")


if __name__ == "__main__":
    unittest.main()
