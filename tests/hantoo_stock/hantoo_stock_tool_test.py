import sys
import unittest
from unittest.mock import patch
from dotenv import load_dotenv
from src.tools.hantoo_stock.tool import HantooFinancialStatementTool
from src.tools.hantoo_stock.hantoo_stock import HantooStockAPIWrapper

# .env 파일 로드
load_dotenv()

# 경로 설정
sys.path.append("..")  # 상위 디렉토리 추가


class TestHantooStockTool(unittest.TestCase):
    """한투 재무제표 분석 도구 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        self.tool = HantooFinancialStatementTool()

    def test_extract_stock_code(self):
        """종목코드 추출 테스트"""
        # 다양한 쿼리 패턴
        testcases = [
            ("삼성전자(005930)의 재무제표 분석해줘", "005930"),
            ("종목코드 005930의 재무상태는?", "005930"),
            ("005930에 대한 재무분석을 해주세요", "005930"),
            ("Stock code: 005930 financial analysis", "005930"),
            ("SK하이닉스 000660 재무제표 보여줘", "000660"),
            ("재무제표 분석", None),  # 종목코드가 없는 경우
        ]

        for query, expected in testcases:
            result = self.tool._extract_stock_code(query)
            self.assertEqual(result, expected, f"Query: {query}")

    @patch.object(HantooStockAPIWrapper, "analyze_financial_statements")
    def test_run_success(self, mock_analyze):
        """도구 실행 성공 테스트"""
        # 목 분석 결과 설정
        mock_analyze.return_value = {
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "balance_sheet": [{"stac_yymm": "202312", "total_aset": "5000000"}],
            "income_statement": [{"stac_yymm": "202312", "sale_account": "1000000"}],
            "financial_ratios": [{"stac_yymm": "202312", "roe_val": "12.5"}],
            "analysis": {
                "current_ratio": "2.00",
                "liquidity_evaluation": "Good liquidity",
                "debt_ratio": "50.00%",
                "debt_evaluation": "Moderate debt",
            },
        }

        # 도구 실행
        result = self.tool._run("삼성전자(005930)의 재무제표 분석해줘")

        # 검증
        self.assertIsInstance(result, str)
        self.assertIn("Financial Statement Analysis for Stock Code 005930", result)
        self.assertIn("Good liquidity", result)
        self.assertIn("Moderate debt", result)

    def test_run_no_stock_code(self):
        """종목코드 없는 경우 테스트"""
        result = self.tool._run("재무제표 분석해줘")
        self.assertIn("No valid stock code", result)

    @patch.object(HantooStockAPIWrapper, "analyze_financial_statements")
    def test_run_api_error(self, mock_analyze):
        """API 오류 발생 시 테스트"""
        mock_analyze.side_effect = Exception("API connection error")

        result = self.tool._run("삼성전자(005930)의 재무제표 분석해줘")
        self.assertIn("Error analyzing financial statements", result)

    @patch.object(HantooStockAPIWrapper, "analyze_financial_statements")
    def test_format_financial_analysis(self, mock_analyze):
        """재무제표 분석 결과 포맷팅 테스트"""
        # 테스트 데이터
        analysis_data = {
            "stock_code": "005930",
            "balance_sheet": [
                {
                    "stac_yymm": "202312",
                    "total_aset": "5000000",
                    "cras": "3000000",
                    "fxas": "2000000",
                    "total_lblt": "2500000",
                    "flow_lblt": "1500000",
                    "total_cptl": "2500000",
                }
            ],
            "income_statement": [
                {
                    "stac_yymm": "202312",
                    "sale_account": "1000000",
                    "sale_cost": "700000",
                    "sale_totl_prfi": "300000",
                    "bsop_prti": "200000",
                    "thtr_ntin": "150000",
                }
            ],
            "financial_ratios": [
                {
                    "stac_yymm": "202312",
                    "roe_val": "12.5",
                    "eps": "5000",
                    "bps": "40000",
                }
            ],
            "analysis": {
                "current_ratio": "2.00",
                "liquidity_evaluation": "Good liquidity",
                "debt_ratio": "50.00%",
                "debt_evaluation": "Moderate debt",
                "operating_margin": "20.00%",
                "profitability_evaluation": "Excellent profitability",
                "roe": "12.50%",
                "roe_evaluation": "Good ROE",
            },
        }

        # 포맷팅 메소드 호출
        formatted_result = self.tool._format_financial_analysis(analysis_data)

        # 검증
        self.assertIn(
            "Financial Statement Analysis for Stock Code 005930", formatted_result
        )
        self.assertIn("Balance Sheet Information", formatted_result)
        self.assertIn("Income Statement Information", formatted_result)
        self.assertIn("Financial Ratios", formatted_result)
        self.assertIn("Financial Analysis", formatted_result)
        self.assertIn("Good liquidity", formatted_result)
        self.assertIn("Moderate debt", formatted_result)
        self.assertIn("Excellent profitability", formatted_result)
        self.assertIn("Good ROE", formatted_result)


if __name__ == "__main__":
    unittest.main()
