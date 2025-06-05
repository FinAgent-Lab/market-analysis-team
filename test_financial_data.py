"""
재무 데이터 존재 여부 확인 테스트 스크립트
"""
import os
import sys
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.tools.supabase_data_reader import get_supabase_reader

def test_financial_data():
    """재무 데이터 존재 여부 테스트"""
    reader = get_supabase_reader()
    
    ticker = "AAPL"
    test_dates = ["2023-02-05", "2023-03-01", "2023-06-01", "2023-09-01"]
    
    print(f"=== {ticker} 재무 데이터 존재 여부 확인 ===")
    
    # 1. 전체 재무 데이터 개수 확인
    try:
        response = reader.client.table("financial_metrics") \
            .select("report_period, period, market_cap, price_to_earnings_ratio") \
            .eq("ticker", ticker) \
            .order("report_period", desc=True) \
            .limit(20) \
            .execute()
        
        print(f"\n📊 {ticker} 전체 재무 데이터: {len(response.data)}건")
        if response.data:
            print("최근 재무 데이터 5건:")
            for i, record in enumerate(response.data[:5]):
                print(f"  {i+1}. {record['report_period']} ({record.get('period', 'N/A')}) - 시가총액: {record.get('market_cap', 'N/A')}, PER: {record.get('price_to_earnings_ratio', 'N/A')}")
    except Exception as e:
        print(f"❌ 전체 데이터 조회 오류: {e}")
    
    # 2. 특정 날짜별 조회 테스트
    for test_date in test_dates:
        print(f"\n📅 {test_date} 이전 최신 재무 데이터 조회:")
        
        try:
            # TTM 데이터 조회
            response = reader.client.table("financial_metrics") \
                .select("report_period, period, market_cap, price_to_earnings_ratio, gross_margin") \
                .eq("ticker", ticker) \
                .lte("report_period", test_date) \
                .eq("period", "ttm") \
                .order("report_period", desc=True) \
                .limit(3) \
                .execute()
            
            if response.data:
                print(f"  TTM 데이터 {len(response.data)}건 발견:")
                for record in response.data:
                    print(f"    - {record['report_period']} (TTM): 시가총액={record.get('market_cap', 'N/A')}, PER={record.get('price_to_earnings_ratio', 'N/A')}")
            else:
                print(f"  TTM 데이터 없음")
                
                # TTM이 없으면 quarterly 조회
                response = reader.client.table("financial_metrics") \
                    .select("report_period, period, market_cap, price_to_earnings_ratio") \
                    .eq("ticker", ticker) \
                    .lte("report_period", test_date) \
                    .eq("period", "quarterly") \
                    .order("report_period", desc=True) \
                    .limit(3) \
                    .execute()
                
                if response.data:
                    print(f"  Quarterly 데이터 {len(response.data)}건 발견:")
                    for record in response.data:
                        print(f"    - {record['report_period']} (Quarterly): 시가총액={record.get('market_cap', 'N/A')}, PER={record.get('price_to_earnings_ratio', 'N/A')}")
                else:
                    print(f"  Quarterly 데이터도 없음")
        
        except Exception as e:
            print(f"  ❌ 조회 오류: {e}")

if __name__ == "__main__":
    test_financial_data()