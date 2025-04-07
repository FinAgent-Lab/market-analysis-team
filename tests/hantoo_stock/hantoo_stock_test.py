import unittest
from unittest.mock import patch, MagicMock
import json
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 경로 설정
import sys
sys.path.append('..')  # 상위 디렉토리 추가

from src.tools.hantoo_stock.hantoo_stock import HantooStockAPIWrapper

class TestHantooStockAPI(unittest.TestCase):
    """한투 API 래퍼 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        # API 키가 환경변수에 설정되어 있는지 확인
        self.api_key_exists = "HANTOO_APP_KEY" in os.environ and "HANTOO_APP_SECRET" in os.environ

        if self.api_key_exists:
            self.api = HantooStockAPIWrapper()
        else:
            print("WARNING: API keys not found. Mocking API responses.")

    @unittest.skip("API keys not configured or invalid")
    def test_get_access_token(self):
        """액세스 토큰 발급 테스트 - 실제 API 호출이 필요하므로 스킵"""
        token = self.api.get_access_token()
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 10)  # 토큰이 유효한 길이인지 확인

    @patch('src.tools.hantoo_stock.hantoo_stock.HantooStockAPIWrapper.get_access_token')
    @patch('requests.get')
    def test_get_stock_info(self, mock_get, mock_get_token):
        """주식 기본 정보 조회 테스트"""
        # 목 응답 설정
        mock_get_token.return_value = "mock_token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "prdt_name": "삼성전자",
                "pdno": "005930",
                "bstp_cls_code": "01"
            },
            "rt_cd": "0"
        }
        mock_get.return_value = mock_response

        # API 래퍼 생성 및 메소드 호출
        api = HantooStockAPIWrapper()
        result = api.get_stock_info("005930")

        # 검증
        self.assertEqual(result["output"]["prdt_name"], "삼성전자")
        self.assertEqual(result["output"]["pdno"], "005930")

    @patch('src.tools.hantoo_stock.hantoo_stock.HantooStockAPIWrapper.get_access_token')
    @patch('requests.get')
    def test_get_balance_sheet(self, mock_get, mock_get_token):
        """대차대조표 조회 테스트"""
        # 목 응답 설정
        mock_get_token.return_value = "mock_token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": [
                {
                    "stac_yymm": "202312",
                    "total_aset": "5000000",
                    "cras": "3000000",
                    "fxas": "2000000",
                    "total_lblt": "2500000",
                    "flow_lblt": "1500000",
                    "total_cptl": "2500000"
                }
            ],
            "rt_cd": "0"
        }
        mock_get.return_value = mock_response

        # API 래퍼 생성 및 메소드 호출
        api = HantooStockAPIWrapper()
        result = api.get_balance_sheet("005930")

        # 검증
        self.assertEqual(result["output"][0]["total_aset"], "5000000")
        self.assertEqual(result["output"][0]["total_cptl"], "2500000")

    @patch('src.tools.hantoo_stock.hantoo_stock.HantooStockAPIWrapper.get_access_token')
    @patch('requests.get')
    def test_get_income_statement(self, mock_get, mock_get_token):
        """손익계산서 조회 테스트"""
        # 목 응답 설정
        mock_get_token.return_value = "mock_token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": [
                {
                    "stac_yymm": "202312",
                    "sale_account": "1000000",
                    "sale_cost": "700000",
                    "sale_totl_prfi": "300000",
                    "bsop_prti": "200000",
                    "thtr_ntin": "150000"
                }
            ],
            "rt_cd": "0"
        }
        mock_get.return_value = mock_response

        # API 래퍼 생성 및 메소드 호출
        api = HantooStockAPIWrapper()
        result = api.get_income_statement("005930")

        # 검증
        self.assertEqual(result["output"][0]["sale_account"], "1000000")
        self.assertEqual(result["output"][0]["thtr_ntin"], "150000")

    @patch('src.tools.hantoo_stock.hantoo_stock.HantooStockAPIWrapper.get_access_token')
    @patch('requests.get')
    def test_analyze_financial_statements(self, mock_get, mock_get_token):
        """재무제표 분석 테스트"""
        # 목 토큰 설정
        mock_get_token.return_value = "mock_token"

        # 여러 API 응답들을 시뮬레이션하기 위한 사이드 이펙트 설정
        def side_effect(*args, **kwargs):
            if "search-stock-info" in args[0]:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "output": {"prdt_name": "삼성전자", "pdno": "005930"}
                }
                return mock_resp
            elif "balance-sheet" in args[0]:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "output": [
                        {
                            "stac_yymm": "202312",
                            "total_aset": "5000000",
                            "cras": "3000000",
                            "fxas": "2000000",
                            "total_lblt": "2500000",
                            "flow_lblt": "1500000",
                            "total_cptl": "2500000"
                        }
                    ]
                }
                return mock_resp
            elif "income-statement" in args[0]:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "output": [
                        {
                            "stac_yymm": "202312",
                            "sale_account": "1000000",
                            "bsop_prti": "200000",
                            "thtr_ntin": "150000"
                        },
                        {
                            "stac_yymm": "202212",
                            "sale_account": "900000",
                            "bsop_prti": "180000",
                            "thtr_ntin": "140000"
                        }
                    ]
                }
                return mock_resp
            elif "financial-ratio" in args[0]:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "output": [
                        {
                            "stac_yymm": "202312",
                            "roe_val": "12.5",
                            "eps": "5000",
                            "bps": "40000"
                        }
                    ]
                }
                return mock_resp

            # 기본 응답
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"output": {}}
            return mock_resp

        mock_get.side_effect = side_effect

        # API 래퍼 생성 및 메소드 호출
        api = HantooStockAPIWrapper()
        result = api.analyze_financial_statements("005930")

        # 검증
        self.assertEqual(result["stock_code"], "005930")
        self.assertIn("analysis", result)

        # 분석 결과 검증
        analysis = result["analysis"]
        self.assertIn("current_ratio", analysis)
        self.assertIn("debt_ratio", analysis)
        self.assertIn("sales_growth", analysis)

if __name__ == '__main__':
    unittest.main()