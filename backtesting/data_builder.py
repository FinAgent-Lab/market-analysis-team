import os
import sys
import time
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Supabase client
from supabase import create_client, Client

# 프로젝트의 기존 모듈 임포트
from src.tools.financial_datasets_connector import (
    get_prices,
    get_financial_metrics,
    get_company_news,
    get_insider_trades,
    get_market_cap
)

# .env 파일에서 환경 변수 로드
load_dotenv()

# --- 설정 ---
TICKERS = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"]
# 기존 데이터와 중복되지 않도록 범위 조정
FULL_START_DATE = "2023-01-01"
FULL_END_DATE = "2025-05-31"
EXISTING_START = "2023-04-01"
EXISTING_END = "2025-04-30"

# Supabase Table Names
SUPABASE_PRICES_TABLE = "stock_prices"
SUPABASE_NEWS_TABLE = "company_news"
SUPABASE_FINANCIALS_TABLE = "financial_metrics"
SUPABASE_INSIDER_TRADES_TABLE = "insider_trades"
SUPABASE_COMPANY_FACTS_TABLE = "company_facts"


def init_supabase() -> Client:
    """Supabase 클라이언트를 초기화합니다."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY 환경 변수가 설정되지 않았습니다.")

    print("Supabase 클라이언트 초기화 중...")
    client: Client = create_client(supabase_url, supabase_key)
    print("Supabase 클라이언트 초기화 완료.")
    return client


def generate_unique_id(parts):
    """주어진 부분들로부터 해시 기반의 고유 ID를 생성합니다."""
    combined_string = "".join(str(p) for p in parts)
    return hashlib.md5(combined_string.encode()).hexdigest()


def collect_missing_data_ranges(start_date: str, end_date: str, existing_start: str, existing_end: str):
    """기존 데이터와 겹치지 않는 범위들을 반환"""
    ranges = []
    
    # 2023-01-01 ~ 2023-03-31 (기존 데이터 이전)
    if start_date < existing_start:
        early_end = "2023-03-31"
        ranges.append((start_date, early_end, "초기 데이터"))
    
    # 2025-05-01 ~ 2025-05-31 (기존 데이터 이후)
    if end_date > existing_end:
        late_start = "2025-05-01"
        ranges.append((late_start, end_date, "최신 데이터"))
    
    return ranges


def fetch_and_upsert_prices(supabase_client: Client, table_name: str, ticker: str, start_date: str, end_date: str):
    """주어진 티커의 가격 정보를 수집하여 Supabase에 업로드합니다."""
    print(f"{ticker}: 가격 정보 수집 중 ({start_date} ~ {end_date})...")
    
    try:
        prices = get_prices(ticker, start_date, end_date)
        records_to_upsert = []

        for price_data in prices:
            record_id = f"price_{ticker}_{price_data.time.split('T')[0]}"
            record = price_data.model_dump()
            record["id"] = record_id
            record["ticker"] = ticker
            records_to_upsert.append(record)

        if records_to_upsert:
            print(f"{ticker}: {len(records_to_upsert)} 건의 가격 정보 업로드 중...")
            try:
                response = supabase_client.table(table_name).upsert(records_to_upsert, on_conflict="id").execute()
                if response.data:
                    print(f"{ticker}: 가격 정보 {len(response.data)}건 업로드/업데이트 완료.")
            except Exception as e:
                print(f"{ticker}: 가격 정보 업로드 중 예외 발생: {e}")
        else:
            print(f"{ticker}: 업로드할 가격 정보 없음.")
            
    except Exception as e:
        print(f"{ticker}: 가격 정보 수집 중 오류: {e}")
    
    print(f"{ticker}: 가격 정보 처리 완료.")


def fetch_and_upsert_news(supabase_client: Client, table_name: str, ticker: str, start_date: str, end_date: str):
    """뉴스를 수집하여 Supabase에 업로드합니다."""
    print(f"{ticker}: 뉴스 정보 수집 중 ({start_date} ~ {end_date})...")
    
    try:
        news_items = get_company_news(ticker, end_date, start_date=start_date, limit=1000)
        records_to_upsert = []
        seen_ids = set()

        for idx, news_item in enumerate(news_items):
            url_hash = generate_unique_id([news_item.url])
            record_id = f"news_{ticker}_{url_hash}"
            
            if record_id in seen_ids:
                record_id = f"news_{ticker}_{url_hash}_{idx}"
            seen_ids.add(record_id)
            
            record = news_item.model_dump()
            if record.get("sentiment") is None:
                record["sentiment"] = ""

            record["id"] = record_id
            record["ticker"] = ticker
            records_to_upsert.append(record)

        if records_to_upsert:
            print(f"{ticker}: {len(records_to_upsert)} 건의 뉴스 정보 업로드 중...")
            try:
                response = supabase_client.table(table_name).upsert(records_to_upsert, on_conflict="id").execute()
                if response.data:
                    print(f"{ticker}: 뉴스 정보 {len(response.data)}건 업로드/업데이트 완료.")
            except Exception as e:
                print(f"{ticker}: 뉴스 정보 업로드 중 예외 발생: {e}")
        else:
            print(f"{ticker}: 업로드할 뉴스 정보 없음.")
            
    except Exception as e:
        print(f"{ticker}: 뉴스 정보 수집 중 오류: {e}")
    
    print(f"{ticker}: 뉴스 정보 처리 완료.")


def fetch_and_upsert_financial_metrics(supabase_client: Client, table_name: str, ticker: str, overall_start_date: str, overall_end_date: str):
    """재무 지표를 수집하여 Supabase에 업로드합니다."""
    print(f"{ticker}: 재무 지표 수집 중 (대상 기간: {overall_start_date} ~ {overall_end_date})...")
    
    try:
        periods_to_fetch = {
            "quarterly": 20,  # 더 많은 분기 데이터
            "annual": 8       # 더 많은 연간 데이터
        }
        all_metrics_to_upsert = []

        for period_type, limit in periods_to_fetch.items():
            print(f"{ticker}: {period_type} 재무 지표 수집 중...")
            metrics_list = get_financial_metrics(ticker, overall_end_date, period=period_type, limit=limit)

            for metric_data in metrics_list:
                report_date_str = metric_data.report_period
                if overall_start_date <= report_date_str <= overall_end_date:
                    record_id = f"financials_{ticker}_{report_date_str}_{period_type}"
                    record = metric_data.model_dump()

                    # NULL 값 처리
                    numeric_fields = {
                        'market_cap', 'enterprise_value', 'price_to_earnings_ratio', 'price_to_book_ratio',
                        'price_to_sales_ratio', 'enterprise_value_to_ebitda_ratio', 'enterprise_value_to_revenue_ratio',
                        'free_cash_flow_yield', 'peg_ratio', 'gross_margin', 'operating_margin', 'net_margin',
                        'return_on_equity', 'return_on_assets', 'return_on_invested_capital', 'asset_turnover',
                        'inventory_turnover', 'receivables_turnover', 'days_sales_outstanding', 'operating_cycle',
                        'working_capital_turnover', 'current_ratio', 'quick_ratio', 'cash_ratio',
                        'operating_cash_flow_ratio', 'debt_to_equity', 'debt_to_assets', 'interest_coverage',
                        'revenue_growth', 'earnings_growth', 'book_value_growth', 'earnings_per_share_growth',
                        'free_cash_flow_growth', 'operating_income_growth', 'ebitda_growth', 'payout_ratio',
                        'earnings_per_share', 'book_value_per_share', 'free_cash_flow_per_share'
                    }

                    for key, value in record.items():
                        if value is None:
                            if key in numeric_fields:
                                record[key] = None
                            else:
                                record[key] = ""

                    record["id"] = record_id
                    record["ticker"] = ticker
                    all_metrics_to_upsert.append(record)

        if all_metrics_to_upsert:
            unique_metrics_dict = {item['id']: item for item in all_metrics_to_upsert}
            unique_metrics_list = list(unique_metrics_dict.values())

            print(f"{ticker}: {len(unique_metrics_list)} 건의 재무 지표 업로드 중...")
            try:
                response = supabase_client.table(table_name).upsert(unique_metrics_list, on_conflict="id").execute()
                if response.data:
                    print(f"{ticker}: 재무 지표 {len(response.data)}건 업로드/업데이트 완료.")
            except Exception as e:
                print(f"{ticker}: 재무 지표 업로드 중 예외 발생: {e}")
        else:
            print(f"{ticker}: 업로드할 재무 지표 없음.")
            
    except Exception as e:
        print(f"{ticker}: 재무 지표 수집 중 오류: {e}")
    
    print(f"{ticker}: 재무 지표 처리 완료.")


def fetch_and_upsert_insider_trades(supabase_client: Client, table_name: str, ticker: str, start_date: str, end_date: str):
    """내부자 거래 정보를 수집하여 Supabase에 업로드합니다."""
    print(f"{ticker}: 내부자 거래 정보 수집 중 ({start_date} ~ {end_date})...")
    
    try:
        trades = get_insider_trades(ticker, end_date, start_date=start_date, limit=2000)
        records_to_upsert = []
        seen_ids = set()

        for idx, trade_data in enumerate(trades):
            key_fields_for_id = [
                ticker,
                trade_data.filing_date or "unknown",
                trade_data.transaction_date or "unknown", 
                trade_data.name or "unknown",
                str(trade_data.transaction_shares or 0),
                trade_data.security_title or "unknown"
            ]
            base_id = generate_unique_id(key_fields_for_id)
            record_id = f"insider_{ticker}_{base_id}"
            
            if record_id in seen_ids:
                record_id = f"insider_{ticker}_{base_id}_{idx}"
            seen_ids.add(record_id)
            
            record = trade_data.model_dump()

            # NULL 값 처리
            numeric_fields = {
                'transaction_shares', 'transaction_price_per_share', 'transaction_value',
                'shares_owned_before_transaction', 'shares_owned_after_transaction'
            }

            for key, value in record.items():
                if value is None:
                    if key in numeric_fields:
                        record[key] = None
                    else:
                        record[key] = ""

            record["id"] = record_id
            record["ticker"] = ticker
            records_to_upsert.append(record)

        if records_to_upsert:
            print(f"{ticker}: {len(records_to_upsert)} 건의 내부자 거래 정보 업로드 중...")
            try:
                response = supabase_client.table(table_name).upsert(records_to_upsert, on_conflict="id").execute()
                if response.data:
                    print(f"{ticker}: 내부자 거래 정보 {len(response.data)}건 업로드/업데이트 완료.")
            except Exception as e:
                print(f"{ticker}: 내부자 거래 정보 업로드 중 예외 발생: {e}")
        else:
            print(f"{ticker}: 업로드할 내부자 거래 정보 없음.")
            
    except Exception as e:
        print(f"{ticker}: 내부자 거래 수집 중 오류: {e}")
    
    print(f"{ticker}: 내부자 거래 정보 처리 완료.")


def fetch_and_upsert_company_facts(supabase_client: Client, table_name: str, ticker: str):
    """회사 기본 정보를 수집하여 Supabase에 업로드합니다."""
    print(f"{ticker}: 회사 기본 정보 수집 중...")
    
    try:
        import requests
        headers = {}
        if api_key := os.environ.get("FINANCIAL_DATASETS_API_KEY"):
            headers["X-API-KEY"] = api_key

        url = f"https://api.financialdatasets.ai/company/facts/?ticker={ticker}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"{ticker}: 회사 정보 조회 실패 - {response.status_code}")
            return

        from src.data.models import CompanyFactsResponse
        data = response.json()
        response_model = CompanyFactsResponse(**data)
        company_facts = response_model.company_facts
        
        record_id = f"facts_{ticker}"
        record = company_facts.model_dump()
        record["id"] = record_id
        record["updated_at"] = datetime.now().isoformat()
        
        print(f"{ticker}: 회사 기본 정보 업로드 중...")
        try:
            response = supabase_client.table(table_name).upsert(record, on_conflict="id").execute()
            if response.data:
                print(f"{ticker}: 회사 기본 정보 업로드/업데이트 완료")
        except Exception as e:
            print(f"{ticker}: 회사 정보 업로드 중 예외 발생: {e}")
            
    except Exception as e:
        print(f"{ticker}: 회사 정보 처리 중 예외 발생: {e}")
    
    print(f"{ticker}: 회사 정보 처리 완료")


if __name__ == "__main__":
    print("=== 백테스팅용 데이터 수집 시작 ===")
    print(f"전체 대상 기간: {FULL_START_DATE} ~ {FULL_END_DATE}")
    print(f"기존 데이터 기간: {EXISTING_START} ~ {EXISTING_END}")
    print(f"대상 종목: {TICKERS}")
    
    # 중복되지 않는 데이터 범위 계산
    missing_ranges = collect_missing_data_ranges(FULL_START_DATE, FULL_END_DATE, EXISTING_START, EXISTING_END)
    
    print(f"수집할 데이터 범위:")
    for start, end, desc in missing_ranges:
        print(f"  - {desc}: {start} ~ {end}")
    
    if not missing_ranges:
        print("❌ 수집할 새로운 데이터 범위가 없습니다.")
        exit(0)
    
    # Supabase 클라이언트 초기화
    supabase_client = init_supabase()
    
    for ticker in TICKERS:
        print(f"\n{'='*60}")
        print(f"종목: {ticker} 데이터 수집 시작")
        print(f"{'='*60}")
        
        try:
            # 회사 기본 정보는 한 번만 업데이트
            fetch_and_upsert_company_facts(supabase_client, SUPABASE_COMPANY_FACTS_TABLE, ticker)
            time.sleep(1)
            
            # 각 범위별로 데이터 수집
            for start_date, end_date, desc in missing_ranges:
                print(f"\n📅 {desc} 기간 수집: {start_date} ~ {end_date}")
                
                # 주가 데이터
                fetch_and_upsert_prices(supabase_client, SUPABASE_PRICES_TABLE, ticker, start_date, end_date)
                time.sleep(1)
                
                # 뉴스 데이터
                fetch_and_upsert_news(supabase_client, SUPABASE_NEWS_TABLE, ticker, start_date, end_date)
                time.sleep(1)
                
                # 내부자 거래
                fetch_and_upsert_insider_trades(supabase_client, SUPABASE_INSIDER_TRADES_TABLE, ticker, start_date, end_date)
                time.sleep(1)
            
            # 재무 지표는 전체 기간으로 수집 (중복 제거는 upsert에서 처리)
            fetch_and_upsert_financial_metrics(supabase_client, SUPABASE_FINANCIALS_TABLE, ticker, FULL_START_DATE, FULL_END_DATE)
            time.sleep(1)
            
            print(f"✅ {ticker}: 모든 데이터 수집 완료")
            
        except Exception as e:
            print(f"❌ {ticker}: 데이터 수집 중 오류 발생: {e}")
            continue
    
    print("\n🎉 모든 종목 데이터 수집 완료!")