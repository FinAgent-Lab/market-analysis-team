"""
2022년 재무제표 데이터 추가 수집 스크립트

2023년 1분기 분석을 위해 2022년 재무 지표 데이터를 수집합니다.
"""

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
from src.tools.financial_datasets_connector import get_financial_metrics

# .env 파일에서 환경 변수 로드
load_dotenv()

# --- 설정 ---
TICKERS = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"]
# 2022년 전체 기간 + 2021년 일부 (더 넓은 범위로 수집)
FINANCIAL_START_DATE = "2021-01-01"
FINANCIAL_END_DATE = "2022-12-31"
SUPABASE_FINANCIALS_TABLE = "financial_metrics"

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

def check_existing_financial_data(supabase_client: Client, ticker: str) -> dict:
    """기존 재무 데이터 확인"""
    try:
        # 2022년 데이터 확인
        response = supabase_client.table(SUPABASE_FINANCIALS_TABLE) \
            .select("report_period, period") \
            .eq("ticker", ticker) \
            .gte("report_period", "2022-01-01") \
            .lte("report_period", "2022-12-31") \
            .execute()
        
        existing_2022 = len(response.data) if response.data else 0
        
        # 2021년 데이터 확인
        response = supabase_client.table(SUPABASE_FINANCIALS_TABLE) \
            .select("report_period, period") \
            .eq("ticker", ticker) \
            .gte("report_period", "2021-01-01") \
            .lte("report_period", "2021-12-31") \
            .execute()
        
        existing_2021 = len(response.data) if response.data else 0
        
        print(f"{ticker}: 기존 2022년 재무 데이터 {existing_2022}건, 2021년 {existing_2021}건")
        
        return {
            "2022": existing_2022,
            "2021": existing_2021,
            "total": existing_2022 + existing_2021
        }
        
    except Exception as e:
        print(f"{ticker}: 기존 데이터 확인 중 오류: {e}")
        return {"2022": 0, "2021": 0, "total": 0}

def fetch_and_upsert_financial_metrics_2022(supabase_client: Client, table_name: str, ticker: str):
    """2022년 재무 지표를 수집하여 Supabase에 업로드합니다."""
    print(f"{ticker}: 2022년 재무 지표 수집 중...")
    
    try:
        # 더 넓은 범위로 수집하여 2022년 데이터 확보
        periods_to_fetch = {
            "quarterly": 30,  # 2022년 Q1~Q4 + 이전 분기들
            "annual": 15,     # 2022년 + 이전 연도들
            "ttm": 30         # TTM 데이터도 수집
        }
        all_metrics_to_upsert = []
        
        for period_type, limit in periods_to_fetch.items():
            print(f"{ticker}: {period_type} 재무 지표 수집 중 (limit: {limit})...")
            
            try:
                # 2022-12-31 기준으로 이전 데이터 수집
                metrics_list = get_financial_metrics(
                    ticker, 
                    end_date="2022-12-31", 
                    period=period_type, 
                    limit=limit
                )
                
                print(f"{ticker}: {period_type} 데이터 {len(metrics_list)}건 수집됨")
                
                for metric_data in metrics_list:
                    report_date_str = metric_data.report_period
                    
                    # 2021-01-01 ~ 2022-12-31 범위의 데이터만 처리
                    if FINANCIAL_START_DATE <= report_date_str <= FINANCIAL_END_DATE:
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
                        
                        # 디버그: 수집된 데이터 확인
                        if len(all_metrics_to_upsert) <= 5:  # 처음 5개만 출력
                            print(f"  수집: {report_date_str} ({period_type}) - 시가총액: {record.get('market_cap', 'N/A')}")
                
                # API 호출 간 대기
                time.sleep(1)
                
            except Exception as e:
                print(f"{ticker}: {period_type} 데이터 수집 중 오류: {e}")
                continue

        if all_metrics_to_upsert:
            # 중복 제거 (같은 ID가 있으면 최신 것으로 덮어쓰기)
            unique_metrics_dict = {item['id']: item for item in all_metrics_to_upsert}
            unique_metrics_list = list(unique_metrics_dict.values())

            print(f"{ticker}: {len(unique_metrics_list)} 건의 2022년 재무 지표 업로드 중...")
            
            # 배치 크기를 작게 하여 안정성 확보
            batch_size = 50
            total_uploaded = 0
            
            for i in range(0, len(unique_metrics_list), batch_size):
                batch = unique_metrics_list[i:i + batch_size]
                
                try:
                    response = supabase_client.table(table_name).upsert(batch, on_conflict="id").execute()
                    if response.data:
                        total_uploaded += len(response.data)
                        print(f"{ticker}: 배치 {i//batch_size + 1} 업로드 완료 ({len(response.data)}건)")
                    
                    time.sleep(0.5)  # 배치 간 대기
                    
                except Exception as e:
                    print(f"{ticker}: 배치 {i//batch_size + 1} 업로드 중 오류: {e}")
                    continue
            
            print(f"{ticker}: 총 {total_uploaded}건의 2022년 재무 지표 업로드/업데이트 완료.")
            
            # 업로드 후 확인
            check_uploaded_data(supabase_client, ticker)
            
        else:
            print(f"{ticker}: 업로드할 2022년 재무 지표 없음.")
            
    except Exception as e:
        print(f"{ticker}: 2022년 재무 지표 수집 중 오류: {e}")
    
    print(f"{ticker}: 2022년 재무 지표 처리 완료.")

def check_uploaded_data(supabase_client: Client, ticker: str):
    """업로드된 데이터 확인"""
    try:
        # 2022년 데이터 확인
        response = supabase_client.table(SUPABASE_FINANCIALS_TABLE) \
            .select("report_period, period, market_cap, price_to_earnings_ratio") \
            .eq("ticker", ticker) \
            .gte("report_period", "2022-01-01") \
            .lte("report_period", "2022-12-31") \
            .order("report_period", desc=True) \
            .execute()
        
        if response.data:
            print(f"{ticker}: 업로드된 2022년 데이터 {len(response.data)}건")
            print("  최근 2022년 데이터 샘플:")
            for record in response.data[:3]:
                print(f"    - {record['report_period']} ({record['period']}): 시가총액={record.get('market_cap', 'N/A')}, PER={record.get('price_to_earnings_ratio', 'N/A')}")
        else:
            print(f"{ticker}: 2022년 데이터가 업로드되지 않았습니다.")
            
    except Exception as e:
        print(f"{ticker}: 업로드 데이터 확인 중 오류: {e}")

def main():
    """2022년 재무 데이터 수집 실행"""
    print("=== 2022년 재무제표 데이터 추가 수집 시작 ===")
    print(f"수집 기간: {FINANCIAL_START_DATE} ~ {FINANCIAL_END_DATE}")
    print(f"대상 종목: {TICKERS}")
    print(f"목적: 2023년 1분기 분석을 위한 기준 데이터 확보")
    
    # Supabase 클라이언트 초기화
    supabase_client = init_supabase()
    
    # 전체 통계
    total_success = 0
    total_errors = 0
    
    for ticker in TICKERS:
        print(f"\n{'='*60}")
        print(f"종목: {ticker} - 2022년 재무 데이터 수집 시작")
        print(f"{'='*60}")
        
        try:
            # 기존 데이터 확인
            existing_data = check_existing_financial_data(supabase_client, ticker)
            
            # 2022년 재무 지표 수집 및 업로드
            fetch_and_upsert_financial_metrics_2022(supabase_client, SUPABASE_FINANCIALS_TABLE, ticker)
            
            print(f"✅ {ticker}: 2022년 재무 데이터 수집 완료")
            total_success += 1
            
            # API 호출 제한 고려하여 대기
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ {ticker}: 2022년 데이터 수집 중 오류 발생: {e}")
            total_errors += 1
            continue
    
    # 최종 통계
    print(f"\n{'='*80}")
    print("🎉 2022년 재무제표 데이터 수집 완료!")
    print(f"📊 최종 통계:")
    print(f"  - 성공: {total_success}개 종목")
    print(f"  - 실패: {total_errors}개 종목")
    print(f"  - 성공률: {(total_success/(total_success+total_errors))*100:.1f}%" if (total_success+total_errors) > 0 else "  - 성공률: N/A")
    
    # 다음 단계 안내
    print(f"\n📋 다음 단계:")
    print(f"1. 2023년 1분기 백테스팅 보고서 테스트:")
    print(f"   python test_financial_data.py")
    print(f"2. 2023년 1분기 보고서 생성:")
    print(f"   cd backtesting && python weekly_batch_generator.py")
    print(f"3. 특정 날짜 보고서 확인:")
    print(f"   cd backtesting && python weekly_reporter.py --ticker AAPL --date 2023-03-15")

if __name__ == "__main__":
    main()