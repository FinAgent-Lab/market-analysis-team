import unittest
from unittest.mock import patch, MagicMock
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 경로 설정
import sys

sys.path.append("..")  # 상위 디렉토리 추가

from src.tools.us_stock.alpha_vantage import AlphaVantageAPIWrapper


class TestAlphaVantageAPI(unittest.TestCase):
    """Alpha Vantage API 래퍼 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        # API 키가 환경변수에 설정되어 있는지 확인
        self.api_key_exists = "ALPHA_VANTAGE_API_KEY" in os.environ

        if self.api_key_exists:
            self.api = AlphaVantageAPIWrapper()
        else:
            print("WARNING: API key not found. Mocking API responses.")

    @unittest.skip("API key not configured or invalid")
    def test_make_request(self):
        """API 요청 테스트 - 실제 API 호출이 필요하므로 스킵"""
        if not self.api_key_exists:
            self.skipTest("API key not configured")

        response = self.api.make_request("OVERVIEW", "AAPL")
        self.assertIsNotNone(response)
        self.assertIn("Symbol", response)

    @patch("requests.get")
    def test_get_company_overview(self, mock_get):
        """회사 개요 조회 테스트"""
        # 목 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Symbol": "AAPL",
            "Name": "Apple Inc",
            "Sector": "Technology",
            "Industry": "Consumer Electronics",
            "MarketCapitalization": "2000000000000",
            "PERatio": "30.25",
            "EPS": "6.15",
            "ReturnOnEquityTTM": "0.15",
        }
        mock_get.return_value = mock_response

        # API 래퍼 생성 및 메소드 호출
        api = AlphaVantageAPIWrapper(api_key="dummy_key")
        result = api.get_company_overview("AAPL")

        # 검증
        self.assertEqual(result["Symbol"], "AAPL")
        self.assertEqual(result["Name"], "Apple Inc")
        self.assertEqual(result["Sector"], "Technology")

    @patch("requests.get")
    def test_get_balance_sheet(self, mock_get):
        """대차대조표 조회 테스트"""
        # 목 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "symbol": "AAPL",
            "annualReports": [
                {
                    "fiscalDateEnding": "2022-09-30",
                    "totalAssets": "352755000000",
                    "totalCurrentAssets": "135405000000",
                    "totalLiabilities": "302083000000",
                    "totalCurrentLiabilities": "153982000000",
                    "totalShareholderEquity": "50672000000",
                }
            ],
            "quarterlyReports": [],
        }
        mock_get.return_value = mock_response

        # API 래퍼 생성 및 메소드 호출
        api = AlphaVantageAPIWrapper(api_key="dummy_key")
        result = api.get_balance_sheet("AAPL")

        # 검증
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["annualReports"][0]["totalAssets"], "352755000000")
        self.assertEqual(
            result["annualReports"][0]["totalShareholderEquity"], "50672000000"
        )

    @patch("requests.get")
    def test_get_income_statement(self, mock_get):
        """손익계산서 조회 테스트"""
        # 목 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "symbol": "AAPL",
            "annualReports": [
                {
                    "fiscalDateEnding": "2022-09-30",
                    "totalRevenue": "394328000000",
                    "costOfRevenue": "223546000000",
                    "grossProfit": "170782000000",
                    "operatingIncome": "119437000000",
                    "netIncome": "99803000000",
                },
                {
                    "fiscalDateEnding": "2021-09-30",
                    "totalRevenue": "365817000000",
                    "costOfRevenue": "212981000000",
                    "grossProfit": "152836000000",
                    "operatingIncome": "108949000000",
                    "netIncome": "94680000000",
                },
            ],
            "quarterlyReports": [],
        }
        mock_get.return_value = mock_response

        # API 래퍼 생성 및 메소드 호출
        api = AlphaVantageAPIWrapper(api_key="dummy_key")
        result = api.get_income_statement("AAPL")

        # 검증
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["annualReports"][0]["totalRevenue"], "394328000000")
        self.assertEqual(result["annualReports"][0]["netIncome"], "99803000000")

    @patch("requests.get")
    def test_get_cash_flow(self, mock_get):
        """현금흐름표 조회 테스트"""
        # 목 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "symbol": "AAPL",
            "annualReports": [
                {
                    "fiscalDateEnding": "2022-09-30",
                    "operatingCashflow": "122151000000",
                    "cashflowFromInvestment": "-22354000000",
                    "cashflowFromFinancing": "-110749000000",
                    "capitalExpenditures": "-11085000000",
                }
            ],
            "quarterlyReports": [],
        }
        mock_get.return_value = mock_response

        # API 래퍼 생성 및 메소드 호출
        api = AlphaVantageAPIWrapper(api_key="dummy_key")
        result = api.get_cash_flow("AAPL")

        # 검증
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(
            result["annualReports"][0]["operatingCashflow"], "122151000000"
        )
        self.assertEqual(
            result["annualReports"][0]["capitalExpenditures"], "-11085000000"
        )

    @patch(
        "src.tools.us_stock.alpha_vantage.AlphaVantageAPIWrapper.get_company_overview"
    )
    @patch("src.tools.us_stock.alpha_vantage.AlphaVantageAPIWrapper.get_balance_sheet")
    @patch(
        "src.tools.us_stock.alpha_vantage.AlphaVantageAPIWrapper.get_income_statement"
    )
    @patch("src.tools.us_stock.alpha_vantage.AlphaVantageAPIWrapper.get_cash_flow")
    def test_analyze_financial_statements(
        self, mock_cash_flow, mock_income, mock_balance, mock_overview
    ):
        """재무제표 분석 테스트"""
        # 각 메소드에 대한 목 응답 설정
        mock_overview.return_value = {
            "Symbol": "AAPL",
            "Name": "Apple Inc",
            "Sector": "Technology",
            "Industry": "Consumer Electronics",
            "MarketCapitalization": "2000000000000",
            "PERatio": "30.25",
            "EPS": "6.15",
            "ReturnOnEquityTTM": "0.15",
            "OperatingMarginTTM": "0.30",
            "ProfitMargin": "0.25",
            "QuarterlyEarningsGrowthYOY": "0.08",
            "QuarterlyRevenueGrowthYOY": "0.06",
        }

        mock_balance.return_value = {
            "symbol": "AAPL",
            "annualReports": [
                {
                    "fiscalDateEnding": "2022-09-30",
                    "totalAssets": "352755000000",
                    "totalCurrentAssets": "135405000000",
                    "totalLiabilities": "302083000000",
                    "totalCurrentLiabilities": "53982000000",
                    "totalShareholderEquity": "50672000000",
                }
            ],
        }

        mock_income.return_value = {
            "symbol": "AAPL",
            "annualReports": [
                {
                    "fiscalDateEnding": "2022-09-30",
                    "totalRevenue": "394328000000",
                    "costOfRevenue": "223546000000",
                    "grossProfit": "170782000000",
                    "operatingIncome": "119437000000",
                    "netIncome": "99803000000",
                },
                {
                    "fiscalDateEnding": "2021-09-30",
                    "totalRevenue": "365817000000",
                    "costOfRevenue": "212981000000",
                    "grossProfit": "152836000000",
                    "operatingIncome": "108949000000",
                    "netIncome": "94680000000",
                },
            ],
        }

        mock_cash_flow.return_value = {
            "symbol": "AAPL",
            "annualReports": [
                {
                    "fiscalDateEnding": "2022-09-30",
                    "operatingCashflow": "122151000000",
                    "cashflowFromInvestment": "-22354000000",
                    "cashflowFromFinancing": "-110749000000",
                    "capitalExpenditures": "-11085000000",
                }
            ],
        }

        # API 래퍼 생성 및 메소드 호출
        api = AlphaVantageAPIWrapper(api_key="dummy_key")
        result = api.analyze_financial_statements("AAPL")

        # 검증
        self.assertEqual(result["ticker"], "AAPL")
        self.assertEqual(result["company_name"], "Apple Inc")
        self.assertIn("profile", result)
        self.assertIn("balance_sheet", result)
        self.assertIn("income_statement", result)
        self.assertIn("cash_flow", result)
        self.assertIn("analysis", result)

        # 분석 결과 검증
        analysis = result["analysis"]

        # 유동성 분석 검증
        self.assertIn("current_ratio", analysis)
        self.assertIn("liquidity_evaluation", analysis)

        # 부채 분석 검증
        self.assertIn("debt_to_equity", analysis)
        self.assertIn("debt_evaluation", analysis)

        # 수익성 분석 검증
        if "operating_margin" in analysis:
            self.assertIn("profitability_evaluation", analysis)

        # 성장성 분석 검증 (매출 성장률)
        self.assertIn("revenue_growth", analysis)
        self.assertIn("revenue_growth_evaluation", analysis)

        # ROE 분석 검증
        if "roe" in analysis:
            self.assertIn("roe_evaluation", analysis)

    @patch("requests.get")
    def test_error_handling(self, mock_get):
        """에러 처리 테스트"""
        # 에러 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Error Message": "Invalid API call. Please retry or visit the documentation."
        }
        mock_get.return_value = mock_response

        # API 래퍼 생성 및 메소드 호출
        api = AlphaVantageAPIWrapper(api_key="dummy_key")
        result = api.get_company_overview("INVALID")

        # 검증
        self.assertIn("error", result)

    @patch("requests.get")
    def test_api_limit_handling(self, mock_get):
        """API 제한 처리 테스트"""
        # API 제한 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute and 500 calls per day."
        }
        mock_get.return_value = mock_response

        # API 래퍼 생성 및 메소드 호출
        api = AlphaVantageAPIWrapper(api_key="dummy_key")
        result = api.get_company_overview("AAPL")

        # 검증
        self.assertIn("error", result)
        self.assertIn("API call frequency", result["error"])

    @patch("requests.get")
    def test_caching(self, mock_get):
        """캐싱 기능 테스트"""
        # 목 응답 설정
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Symbol": "MSFT",
            "Name": "Microsoft Corporation",
            "Sector": "Technology",
        }
        mock_get.return_value = mock_response

        # API 래퍼 생성
        api = AlphaVantageAPIWrapper(api_key="dummy_key")

        # 첫 번째 호출
        api.get_company_overview("MSFT")

        # 두 번째 호출 (캐시에서 가져와야 함)
        api.get_company_overview("MSFT")

        # requests.get은 한 번만 호출되어야 함
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
