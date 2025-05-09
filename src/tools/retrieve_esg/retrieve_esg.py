"""Utility for retrieving ESG data.

Retrieves ESG data for a given ticker from  yfinance API.
Supports both synchronous and asynchronous methods.
"""

import datetime
from typing import Dict, Any

import yfinance as yf
from pydantic import BaseModel, ConfigDict

# from core.db import get_async_session, get_sync_session
# from model.esg_data import ESGData


class ESGSearchWrapper(BaseModel):
    """Wrapper class for ESG data search."""

    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    # 비동기 메서드
    async def get_from_yfinance_async(self, ticker: str) -> Dict[str, Any]:
        """Asynchronously retrieve the latest ESG data from the yfinance API.

        Args:
            ticker: Stock ticker symbol to search for

        Returns:
            ESG data dictionary
        """
        try:
            ticker = ticker.upper()
            # yfinance는 기본적으로 동기식 API이므로, 별도의 쓰레드에서 실행해야 할 수 있습니다.
            ticker_obj = yf.Ticker(ticker)
            esg_data = ticker_obj.sustainability

            if esg_data is None:
                return {
                    "ticker": ticker,
                    "error": f"{ticker}에 대한 ESG 데이터를 찾을 수 없습니다.",
                }

            # DataFrame을 딕셔너리로 변환
            esg_dict = esg_data.to_dict()
            if not esg_dict:
                return {
                    "ticker": ticker,
                    "error": f"{ticker}에 대한 ESG 데이터를 찾을 수 없습니다.",
                }

            # 첫 번째 열 데이터만 추출
            column_name = list(esg_dict.keys())[0]
            esg_values = esg_dict[column_name]

            # 현재 연도와 월 추가
            now = datetime.datetime.now()

            result = {
                "ticker": ticker,
                "total_esg": esg_values.get("totalEsg"),
                "environment_score": esg_values.get("environmentScore"),
                "social_score": esg_values.get("socialScore"),
                "governance_score": esg_values.get("governanceScore"),
                "rating_year": now.year,
                "rating_month": now.month,
                "records": [],  # 일관성을 위한 빈 records 배열 추가
            }

            return result
        except Exception as e:
            return {
                "ticker": ticker,
                "error": f"yfinance API 호출 중 오류 발생: {str(e)}",
            }

    # 동기 메서드
    def get_from_yfinance_sync(self, ticker: str) -> Dict[str, Any]:
        """Synchronously retrieve the latest ESG data from the yfinance API.

        Args:
            ticker: Stock ticker symbol to search for

        Returns:
            ESG data dictionary
        """
        try:
            ticker = ticker.upper()
            ticker_obj = yf.Ticker(ticker)
            esg_data = ticker_obj.sustainability

            if esg_data is None:
                return {
                    "ticker": ticker,
                    "error": f"{ticker}에 대한 ESG 데이터를 찾을 수 없습니다.",
                }

            # DataFrame을 딕셔너리로 변환
            esg_dict = esg_data.to_dict()
            if not esg_dict:
                return {
                    "ticker": ticker,
                    "error": f"{ticker}에 대한 ESG 데이터를 찾을 수 없습니다.",
                }

            # 첫 번째 열 데이터만 추출
            column_name = list(esg_dict.keys())[0]
            esg_values = esg_dict[column_name]

            # 현재 연도와 월 추가
            now = datetime.datetime.now()

            result = {
                "ticker": ticker,
                "total_esg": esg_values.get("totalEsg"),
                "environment_score": esg_values.get("environmentScore"),
                "social_score": esg_values.get("socialScore"),
                "governance_score": esg_values.get("governanceScore"),
                "rating_year": now.year,
                "rating_month": now.month,
                "records": [],  # 일관성을 위한 빈 records 배열 추가
            }

            return result
        except Exception as e:
            return {
                "ticker": ticker,
                "error": f"yfinance API 호출 중 오류 발생: {str(e)}",
            }

    # 주요 비동기 메서드
    async def get_esg_data_async(
        self, ticker: str, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Asynchronously retrieve ESG data for the given ticker.
        First checks the database, and if the data is not found or a forced refresh is requested, retrieves from yfinance.

        Args:
            ticker: Stock ticker symbol to search for
            force_refresh: Whether to retrieve new data from yfinance even if it exists in the database

        Returns:
            ESG data
        """
        ticker = ticker.upper()

        yf_result = await self.get_from_yfinance_async(ticker)

        return yf_result

    # 주요 동기 메서드
    def get_esg_data_sync(
        self, ticker: str, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Synchronously retrieve ESG data for the given ticker.
        First checks the database, and if the data is not found or a forced refresh is requested, retrieves from yfinance.

        Args:
            ticker: Stock ticker symbol to search for
            force_refresh: Whether to retrieve new data from yfinance even if it exists in the database

        Returns:
            ESG data
        """
        ticker = ticker.upper()

        # 데이터베이스에 없거나 강제 새로고침이 요청된 경우 yfinance에서 가져오기
        yf_result = self.get_from_yfinance_sync(ticker)

        return yf_result
