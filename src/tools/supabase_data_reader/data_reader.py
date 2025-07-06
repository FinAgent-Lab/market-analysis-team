import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class SupabaseDataReader:
    """Supabase 데이터베이스에서 백테스팅 데이터를 조회하는 클래스"""

    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY 환경 변수가 설정되지 않았습니다."
            )

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def get_stock_prices(
        self, ticker: str, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """주가 데이터 조회"""
        try:
            response = (
                self.client.table("stock_prices")
                .select("*")
                .eq("ticker", ticker)
                .gte("time", start_date)
                .lte("time", end_date)
                .order("time", desc=False)
                .execute()
            )

            return response.data if response.data else []
        except Exception as e:
            print(f"주가 데이터 조회 오류: {e}")
            return []

    def get_financial_metrics(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        period: Optional[str] = None,
        limit_count: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """재무 지표 조회. end_date 이전 최신 데이터를 가져오려면 start_date를 과거로, limit_count=1, desc=True로 설정."""
        try:
            query = (
                self.client.table("financial_metrics")
                .select("*")
                .eq("ticker", ticker)
                .lte("report_period", end_date)
            )  # end_date 이전 데이터

            if (
                start_date and start_date != "1970-01-01"
            ):  # start_date가 유효한 경우 필터링 (1970-01-01은 모든 과거를 의미)
                query = query.gte("report_period", start_date)

            if period:
                query = query.eq("period", period)

            # 최신 데이터를 가져오기 위해 report_period 기준 내림차순 정렬
            query = query.order("report_period", desc=True)

            if limit_count:
                query = query.limit(limit_count)

            response = query.execute()

            # 디버깅: 실제 조회된 데이터 출력
            print(
                f"DEBUG: Financial metrics query for {ticker} (end_date: {end_date}, period: {period}, limit: {limit_count})"
            )
            print(
                f"DEBUG: Query result count: {len(response.data) if response.data else 0}"
            )
            if response.data:
                print(f"DEBUG: First financial record: {response.data[0]}")
            else:
                print(f"DEBUG: No financial data found for {ticker}")

            return response.data if response.data else []
        except Exception as e:
            print(f"재무 지표 조회 오류: {e}")
            return []

    def get_company_news(
        self, ticker: str, start_date: str, end_date: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """회사 뉴스 조회"""
        try:
            response = (
                self.client.table("company_news")
                .select("*")
                .eq("ticker", ticker)
                .gte("date", start_date)
                .lte("date", end_date)
                .order("date", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data if response.data else []
        except Exception as e:
            print(f"뉴스 데이터 조회 오류: {e}")
            return []

    def get_insider_trades(
        self, ticker: str, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """내부자 거래 조회"""
        try:
            response = (
                self.client.table("insider_trades")
                .select("*")
                .eq("ticker", ticker)
                .gte("filing_date", start_date)
                .lte("filing_date", end_date)
                .order("filing_date", desc=True)
                .execute()
            )

            return response.data if response.data else []
        except Exception as e:
            print(f"내부자 거래 조회 오류: {e}")
            return []

    def get_company_facts(self, ticker: str) -> Dict[str, Any]:
        """회사 기본 정보 조회"""
        try:
            response = (
                self.client.table("company_facts")
                .select("*")
                .eq("ticker", ticker)
                .execute()
            )

            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"회사 정보 조회 오류: {e}")
            return {}

    def get_weekly_data_summary(self, ticker: str, end_date: str) -> Dict[str, Any]:
        """주간 데이터 요약 (지난 7일간, 재무 데이터는 end_date 기준 최신)"""
        start_date_prices_news_insider = (
            datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=7)
        ).strftime("%Y-%m-%d")

        # 재무 데이터 조회 전략 개선
        financial_metrics_data = {}
        financial_metrics_report_date = "N/A"

        # 1) 먼저 해당 날짜 이전의 데이터 조회 (원칙적인 백테스팅)
        latest_financials = self._get_financial_data_before_date(ticker, end_date)

        # 2) 이전 데이터가 없으면 가장 가까운 미래 데이터 조회 (분석 목적)
        if not latest_financials:
            print(
                f"DEBUG: No financial data before {end_date}, searching for nearest future data..."
            )
            latest_financials = self._get_nearest_financial_data(ticker, end_date)

        if (
            latest_financials
            and isinstance(latest_financials, list)
            and len(latest_financials) > 0
        ):
            financial_metrics_data = latest_financials[0]
            financial_metrics_report_date = financial_metrics_data.get(
                "report_period", "N/A"
            )
            # 디버깅: 재무 데이터 확인
            print(
                f"DEBUG: Found financial data for {ticker}: report_period={financial_metrics_report_date}, period={financial_metrics_data.get('period', 'N/A')}"
            )
            print(
                f"DEBUG: Sample financial metrics: market_cap={financial_metrics_data.get('market_cap', 'N/A')}, pe_ratio={financial_metrics_data.get('price_to_earnings_ratio', 'N/A')}"
            )
        else:
            print(f"DEBUG: No financial metrics found for {ticker} in any time range")

        return {
            "ticker": ticker,
            "period": f"{start_date_prices_news_insider} ~ {end_date}",  # 주가, 뉴스, 내부자거래용 기간
            "report_date_original": end_date,  # 보고서 요청된 기준일
            "prices": self.get_stock_prices(
                ticker, start_date_prices_news_insider, end_date
            ),
            "news": self.get_company_news(
                ticker, start_date_prices_news_insider, end_date, limit=20
            ),
            "insider_trades": self.get_insider_trades(
                ticker, start_date_prices_news_insider, end_date
            ),
            "company_facts": self.get_company_facts(ticker),
            "financial_metrics": financial_metrics_data,
            "report_date_for_financials": financial_metrics_report_date,
        }

    def _get_financial_data_before_date(
        self, ticker: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """해당 날짜 이전의 재무 데이터 조회 (백테스팅 원칙)"""
        # TTM -> Quarterly -> Annual -> All periods 순으로 조회
        for period in ["ttm", "quarterly", "annual", None]:
            financials = self.get_financial_metrics(
                ticker, "1970-01-01", end_date, period=period, limit_count=3
            )
            if financials:
                return financials
        return []

    def _get_nearest_financial_data(
        self, ticker: str, reference_date: str
    ) -> List[Dict[str, Any]]:
        """참조 날짜에서 가장 가까운 재무 데이터 조회 (이전 또는 이후)"""
        try:
            # 1) 가장 가까운 미래 데이터 조회
            query = (
                self.client.table("financial_metrics")
                .select("*")
                .eq("ticker", ticker)
                .gte("report_period", reference_date)
                .order("report_period", desc=False)
                .limit(3)
            )

            response = query.execute()

            if response.data:
                print(
                    f"DEBUG: Found {len(response.data)} future financial records for {ticker} after {reference_date}"
                )
                return response.data

            # 2) 미래 데이터도 없으면 전체에서 가장 가까운 데이터 조회
            query = (
                self.client.table("financial_metrics")
                .select("*")
                .eq("ticker", ticker)
                .order("report_period", desc=True)
                .limit(3)
            )

            response = query.execute()

            if response.data:
                print(f"DEBUG: Using most recent available financial data for {ticker}")
                return response.data

            return []
        except Exception as e:
            print(f"가장 가까운 재무 데이터 조회 오류: {e}")
            return []

    def get_monthly_data_summary(self, ticker: str, end_date: str) -> Dict[str, Any]:
        """월간 데이터 요약 (지난 30일간)"""
        start_date = (
            datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=30)
        ).strftime("%Y-%m-%d")

        return {
            "ticker": ticker,
            "period": f"{start_date} ~ {end_date}",
            "prices": self.get_stock_prices(ticker, start_date, end_date),
            "financial_metrics": self.get_financial_metrics(
                ticker, start_date, end_date
            ),
            "news": self.get_company_news(ticker, start_date, end_date, limit=50),
            "insider_trades": self.get_insider_trades(ticker, start_date, end_date),
            "company_facts": self.get_company_facts(ticker),
        }


# 전역 인스턴스
_data_reader = None


def get_supabase_reader() -> SupabaseDataReader:
    """Supabase 데이터 리더 싱글톤 인스턴스 반환"""
    global _data_reader
    if _data_reader is None:
        _data_reader = SupabaseDataReader()
    return _data_reader
