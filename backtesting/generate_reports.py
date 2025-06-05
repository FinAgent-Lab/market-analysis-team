"""
백테스팅 주간 보고서 일괄 생성 스크립트

여러 종목과 기간에 대해 백테스팅 보고서를 일괄 생성합니다.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from weekly_reporter import BacktestingWeeklyReporter

def generate_date_range(start_date: str, end_date: str, interval_days: int = 7) -> List[str]:
    """날짜 범위에서 주간 간격으로 날짜 리스트 생성"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=interval_days)
    
    return dates

def main():
    """백테스팅 보고서 일괄 생성"""
    # 설정
    TICKERS = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"]
    START_DATE = "2024-01-01"
    END_DATE = "2024-12-31"
    INTERVAL_WEEKS = 4  # 4주마다 보고서 생성
    
    reporter = BacktestingWeeklyReporter()
    
    print("🔬 백테스팅 주간 보고서 일괄 생성 시작")
    print(f"📊 대상 종목: {', '.join(TICKERS)}")
    print(f"📅 기간: {START_DATE} ~ {END_DATE}")
    print(f"🔄 간격: {INTERVAL_WEEKS}주마다")
    print("=" * 60)
    
    # 날짜 리스트 생성
    report_dates = generate_date_range(START_DATE, END_DATE, INTERVAL_WEEKS * 7)
    
    total_reports = len(TICKERS) * len(report_dates)
    current_count = 0
    
    for ticker in TICKERS:
        print(f"\n📈 {ticker} 종목 보고서 생성 중...")
        
        for date in report_dates:
            current_count += 1
            print(f"[{current_count}/{total_reports}] {ticker} - {date}")
            
            try:
                report = reporter.generate_weekly_report(ticker, date)
                
                # 파일로도 저장 (선택사항)
                output_dir = f"backtesting/reports/{ticker}"
                os.makedirs(output_dir, exist_ok=True)
                
                with open(f"{output_dir}/weekly_report_{date}.md", "w", encoding="utf-8") as f:
                    f.write(report)
                
                print(f"  ✅ 완료: {date}")
                
            except Exception as e:
                print(f"  ❌ 실패: {date} - {e}")
                continue
    
    print("\n" + "=" * 60)
    print(f"🎉 백테스팅 보고서 일괄 생성 완료!")
    print(f"📊 총 {current_count}개 보고서 처리")

if __name__ == "__main__":
    main()