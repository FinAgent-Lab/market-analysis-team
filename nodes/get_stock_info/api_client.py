import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

class KoreaInvestmentAPI:
    """한국투자증권 API 클라이언트"""

    def __init__(self):
        """API 인증 정보 및 기본 설정 초기화"""
        load_dotenv()
        self.api_key = os.getenv('KOREA_INVESTMENT_API_KEY')
        self.api_secret = os.getenv('KOREA_INVESTMENT_API_SECRET')
        self.account_number = os.getenv('KOREA_INVESTMENT_ACCOUNT_NUMBER')

        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None
        self.token_issued_at = None
        self.token_expires_in = 86400  # 24시간 (초)

        # 토큰 발급
        self._get_access_token()

    def _get_access_token(self):
        """API 접근을 위한 액세스 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"

        headers = {
            "content-type": "application/json"
        }

        body = {
            "grant_type": "client_credentials",
            "appkey": self.api_key,
            "appsecret": self.api_secret
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(body))
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data.get('access_token')
            self.token_issued_at = datetime.now()
            print("액세스 토큰이 성공적으로 발급되었습니다.")

        except requests.exceptions.RequestException as e:
            print(f"토큰 발급 실패: {e}")
            # 개발/테스트용 임시 토큰
            self.access_token = "DEMO_TOKEN"

    def _check_token_validity(self):
        """액세스 토큰의 유효성 확인 및 필요시 재발급"""
        if not self.token_issued_at:
            self._get_access_token()
            return

        # 토큰 만료 시간 계산 (만료 10분 전에 갱신)
        expiry_time = self.token_issued_at + timedelta(seconds=self.token_expires_in - 600)

        if datetime.now() >= expiry_time:
            print("토큰이 곧 만료됩니다. 토큰을 재발급합니다.")
            self._get_access_token()

    def get_stock_price(self, stock_code):
        """
        실시간 주가 정보 조회

        Args:
            stock_code (str): 종목코드 (예: '005930' for 삼성전자)

        Returns:
            dict: 종목 가격 정보
        """
        self._check_token_validity()

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.api_key,
            "appsecret": self.api_secret,
            "tr_id": "FHKST01010100"
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 주식 시장 구분
            "FID_INPUT_ISCD": stock_code    # 종목코드
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            return data.get('output', {})

        except requests.exceptions.RequestException as e:
            print(f"주가 정보 조회 실패: {e}")
            return {}

    def get_stock_daily_prices(self, stock_code, start_date=None, end_date=None):
        """
        일별 주가 정보 조회

        Args:
            stock_code (str): 종목코드
            start_date (str, optional): 시작일 (YYYYMMDD 형식)
            end_date (str, optional): 종료일 (YYYYMMDD 형식)

        Returns:
            list: 일별 주가 정보 리스트
        """
        self._check_token_validity()

        # 날짜 설정
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        if not start_date:
            # 기본값: 1년
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.api_key,
            "appsecret": self.api_secret,
            "tr_id": "FHKST01010400"
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 주식 시장 구분
            "FID_INPUT_ISCD": stock_code,    # 종목코드
            "FID_PERIOD_DIV_CODE": "D",     # 일봉 조회
            "FID_ORG_ADJ_PRC": "1",         # 수정주가 적용
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            return data.get('output', [])

        except requests.exceptions.RequestException as e:
            print(f"일별 주가 정보 조회 실패: {e}")
            return []

    def get_financial_summary(self, stock_code):
        """
        기업의 재무 정보 요약 조회

        Args:
            stock_code (str): 종목코드

        Returns:
            dict: 재무 정보 요약
        """
        self._check_token_validity()

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-financial-summary"

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.api_key,
            "appsecret": self.api_secret,
            "tr_id": "FHKST03010100"
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 주식 시장 구분
            "FID_INPUT_ISCD": stock_code    # 종목코드
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            return data.get('output', {})

        except requests.exceptions.RequestException as e:
            print(f"재무 정보 조회 실패: {e}")
            return {}