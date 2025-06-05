"""
2022년 재무 데이터 존재 여부 확인 테스트 스크립트
"""
import os
import sys
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.tools.supabase_data_reader import get_supabase_reader

def test_2022_financial_data():
    """2022년 재무 데이터 존재 여부 테스트"""
    reader = get_supabase_reader()
    
    ticker = "AAPL"
    # 2023년 1분기 분석에 필요한 기준 날짜들
    test_dates = ["2023-01-15", "2023-02-15", "2023-03-15", "2023-03-31"]
    
    print(f"=== {ticker} 2022년 재무 데이터 존재 여부 확인 ===")
    
    # 1. 2022년 전체 재무 데이터 개수 확인
    try:
        response = reader.client.table("financial_metrics") \
            .select("report_period, period, market_cap, price_to_earnings_ratio") \
            .eq("ticker", ticker) \
            .gte("report_period", "2022-01-01") \
            .lte("report_period", "2022-12-31") \
            .order("report_period", desc=True) \
            .execute()
        
        print(f"\n📊 {ticker} 2022년 재무 데이터: {len(response.data)}건")
        if response.data:
            print("2022년 재무 데이터 샘플:")
            for i, record in enumerate(response.data[:8]):
                print(f"  {i+1}. {record['report_period']} ({record.get('period', 'N/A')}) - 시가총액: {record.get('market_cap', 'N/A')}, PER: {record.get('price_to_earnings_ratio', 'N/A')}")
    except Exception as e:
        print(f"❌ 2022년 데이터 조회 오류: {e}")
    
    # 2. 2023년 1분기 각 날짜에서 사용 가능한 최신 데이터 확인
    for test_date in test_dates:
        print(f"\n📅 {test_date} 기준 사용 가능한 최신 재무 데이터:")
        
        try:
            # 해당 날짜 이전의 가장 최신 데이터 조회
            response = reader.client.table("financial_metrics") \
                .select("report_period, period, market_cap, price_to_earnings_ratio, gross_margin") \
                .eq("ticker", ticker) \
                .lte("report_period", test_date) \
                .order("report_period", desc=True) \
                .limit(5) \
                .execute()
            
            if response.data:
                print(f"  사용 가능한 데이터 {len(response.data)}건:")
                for record in response.data:
                    print(f"    - {record['report_period']} ({record.get('period', 'N/A')}): 시가총액={record.get('market_cap', 'N/A')}, PER={record.get('price_to_earnings_ratio', 'N/A')}")
            else:
                print(f"  ❌ {test_date} 이전 데이터 없음")
        
        except Exception as e:
            print(f"  ❌ {test_date} 조회 오류: {e}")
    
    # 3. 모든 종목에 대한 2022년 데이터 확인
    print(f"\n📊 모든 종목 2022년 재무 데이터 현황:")
    tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"]
    
    for ticker in tickers:
        try:
            response = reader.client.table("financial_metrics") \
                .select("report_period") \
                .eq("ticker", ticker) \
                .gte("report_period", "2022-01-01") \
                .lte("report_period", "2022-12-31") \
                .execute()
            
            count = len(response.data) if response.data else 0
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {ticker}: {count}건")
            
        except Exception as e:
            print(f"  ❌ {ticker}: 조회 오류 - {e}")

def test_data_coverage_for_2023_q1():
    """2023년 1분기 분석을 위한 데이터 커버리지 테스트"""
    reader = get_supabase_reader()
    
    print(f"\n{'='*60}")
    print("2023년 1분기 분석을 위한 데이터 커버리지 테스트")
    print(f"{'='*60}")
    
    tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"]
    q1_dates = ["2023-01-08", "2023-01-15", "2023-02-05", "2023-02-26", "2023-03-19", "2023-03-31"]
    
    for ticker in tickers:
        print(f"\n📈 {ticker} - 2023년 1분기 데이터 커버리지:")
        
        coverage_good = 0
        coverage_total = len(q1_dates)
        
        for date in q1_dates:
            try:
                # 해당 날짜에서 사용 가능한 최신 재무 데이터 확인
                response = reader.client.table("financial_metrics") \
                    .select("report_period, period") \
                    .eq("ticker", ticker) \
                    .lte("report_period", date) \
                    .order("report_period", desc=True) \
                    .limit(1) \
                    .execute()
                
                if response.data:
                    latest_data = response.data[0]
                    print(f"  {date}: ✅ {latest_data['report_period']} ({latest_data['period']})")
                    coverage_good += 1
                else:
                    print(f"  {date}: ❌ 데이터 없음")
                    
            except Exception as e:
                print(f"  {date}: ❌ 오류 - {e}")
        
        coverage_rate = (coverage_good / coverage_total) * 100
        status = "✅" if coverage_rate >= 80 else "⚠️" if coverage_rate >= 50 else "❌"
        print(f"  {status} 커버리지: {coverage_good}/{coverage_total} ({coverage_rate:.1f}%)")

if __name__ == "__main__":
    test_2022_financial_data()
    test_data_coverage_for_2023_q1()