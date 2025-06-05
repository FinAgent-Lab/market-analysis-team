"""
백테스팅 주간 보고서 일괄 생성 스크립트 (1주 간격)

2023-01-01부터 2025-05-31까지 1주 간격으로 백테스팅 보고서를 생성합니다.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List
import time

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from weekly_reporter import BacktestingWeeklyReporter

def generate_weekly_dates(start_date: str, end_date: str) -> List[str]:
    """시작일부터 종료일까지 1주 간격으로 날짜 리스트 생성"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    dates = []
    current = start
    
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=7)  # 1주 간격
    
    return dates

def check_existing_reports(reporter, ticker: str, dates: List[str]) -> List[str]:
    """이미 생성된 보고서를 확인하고 생성되지 않은 날짜만 반환"""
    try:
        from src.tools.supabase_data_reader import get_supabase_reader
        reader = get_supabase_reader()
        
        # 기존 보고서 조회
        response = reader.client.table("stock_reports") \
            .select("report_date") \
            .eq("ticker", ticker) \
            .eq("report_type", "backtesting_weekly") \
            .execute()
        
        existing_dates = {report["report_date"] for report in response.data} if response.data else set()
        
        # 생성되지 않은 날짜만 필터링
        missing_dates = [date for date in dates if date not in existing_dates]
        
        print(f"{ticker}: 기존 보고서 {len(existing_dates)}개, 생성할 보고서 {len(missing_dates)}개")
        return missing_dates
        
    except Exception as e:
        print(f"{ticker}: 기존 보고서 확인 중 오류: {e}")
        return dates  # 오류 시 모든 날짜 반환

def main():
    """백테스팅 주간 보고서 일괄 생성"""
    # 설정
    TICKERS = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"]
    START_DATE = "2023-01-01"
    END_DATE = "2025-05-31"
    MODEL_NAME = "openai/gpt-4o-mini"  # 기본 모델
    
    print("🔬 백테스팅 주간 보고서 일괄 생성 시작")
    print(f"📊 대상 종목: {', '.join(TICKERS)}")
    print(f"📅 기간: {START_DATE} ~ {END_DATE}")
    print(f"🔄 간격: 1주마다")
    print(f"🤖 AI 모델: {MODEL_NAME}")
    print("=" * 80)
    
    # 주간 날짜 리스트 생성
    all_dates = generate_weekly_dates(START_DATE, END_DATE)
    print(f"📋 총 생성 대상 주차: {len(all_dates)}개")
    
    # 보고서 생성기 초기화
    reporter = BacktestingWeeklyReporter(model_name=MODEL_NAME)
    
    # 전체 통계
    total_reports_to_generate = 0
    total_reports_generated = 0
    total_errors = 0
    
    for ticker in TICKERS:
        print(f"\n📈 {ticker} 종목 보고서 생성 중...")
        print("-" * 60)
        
        # 기존 보고서 확인 및 누락된 날짜만 필터링
        missing_dates = check_existing_reports(reporter, ticker, all_dates)
        
        if not missing_dates:
            print(f"✅ {ticker}: 모든 보고서가 이미 생성되어 있습니다.")
            continue
        
        total_reports_to_generate += len(missing_dates)
        ticker_success = 0
        ticker_errors = 0
        
        for i, date in enumerate(missing_dates, 1):
            try:
                print(f"[{i}/{len(missing_dates)}] {ticker} - {date} 생성 중...")
                
                # 보고서 생성
                report = reporter.generate_weekly_report(ticker, date)
                
                # 생성 실패 확인
                if report.startswith("❌"):
                    print(f"  ⚠️  데이터 없음: {date}")
                    ticker_errors += 1
                    continue
                
                # 보고서 길이 확인 (너무 짧으면 오류로 간주)
                if len(report) < 500:
                    print(f"  ⚠️  보고서가 너무 짧음: {date} ({len(report)} chars)")
                    ticker_errors += 1
                    continue
                
                print(f"  ✅ 완료: {date} ({len(report)} chars)")
                ticker_success += 1
                total_reports_generated += 1
                
                # API 제한 고려하여 잠시 대기
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ 실패: {date} - {e}")
                ticker_errors += 1
                total_errors += 1
                continue
        
        print(f"\n📊 {ticker} 결과: 성공 {ticker_success}개, 실패 {ticker_errors}개")
    
    # 최종 통계
    print("\n" + "=" * 80)
    print("🎉 백테스팅 주간 보고서 일괄 생성 완료!")
    print(f"📊 최종 통계:")
    print(f"  - 총 생성 대상: {total_reports_to_generate}개 보고서")
    print(f"  - 성공적으로 생성: {total_reports_generated}개")
    print(f"  - 실패: {total_errors}개")
    print(f"  - 성공률: {(total_reports_generated/total_reports_to_generate)*100:.1f}%" if total_reports_to_generate > 0 else "  - 성공률: N/A")
    
    # 생성된 보고서 요약
    try:
        from src.tools.supabase_data_reader import get_supabase_reader
        reader = get_supabase_reader()
        
        response = reader.client.table("stock_reports") \
            .select("ticker, report_date") \
            .eq("report_type", "backtesting_weekly") \
            .order("created_at", desc=True) \
            .limit(10) \
            .execute()
        
        if response.data:
            print(f"\n📋 최근 생성된 보고서 (최대 10개):")
            for report in response.data:
                print(f"  - {report['ticker']}: {report['report_date']}")
        
    except Exception as e:
        print(f"\n⚠️  보고서 요약 조회 실패: {e}")

if __name__ == "__main__":
    main()