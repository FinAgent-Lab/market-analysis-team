"""
백테스팅 주간 보고서 일괄 생성 스크립트 (월요일-일요일 기준)

2023-01-01부터 2025-05-31까지 완전한 주간 단위(월요일-일요일)로 백테스팅 보고서를 생성합니다.
불완전한 첫 주나 마지막 주는 건너뜁니다.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Tuple
import time
from weekly_reporter import BacktestingWeeklyReporter

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def get_monday_of_week(date: datetime) -> datetime:
    """주어진 날짜가 속한 주의 월요일을 반환"""
    days_since_monday = date.weekday()  # 월요일: 0, 화요일: 1, ..., 일요일: 6
    monday = date - timedelta(days=days_since_monday)
    return monday

def get_sunday_of_week(date: datetime) -> datetime:
    """주어진 날짜가 속한 주의 일요일을 반환"""
    days_since_monday = date.weekday()
    sunday = date + timedelta(days=(6 - days_since_monday))
    return sunday

def generate_complete_weekly_dates(start_date: str, end_date: str) -> List[Tuple[str, str, str]]:
    """
    완전한 주간 단위(월요일-일요일)로 날짜 범위 생성
    
    Args:
        start_date: 전체 기간 시작일
        end_date: 전체 기간 종료일
    
    Returns:
        List of tuples: (monday_date, sunday_date, report_date)
        report_date는 해당 주의 일요일 (주간 보고서 기준일)
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # 첫 번째 완전한 주의 월요일 찾기
    first_monday = get_monday_of_week(start)
    if first_monday < start:
        # 시작일이 주 중간이면 다음 주 월요일부터 시작
        first_monday += timedelta(days=7)
    
    # 마지막 완전한 주의 일요일 찾기
    last_sunday = get_sunday_of_week(end)
    if last_sunday > end:
        # 종료일이 주 중간이면 이전 주 일요일까지만
        last_sunday -= timedelta(days=7)
    
    weeks = []
    current_monday = first_monday
    
    while current_monday <= last_sunday:
        current_sunday = current_monday + timedelta(days=6)
        
        # 완전한 주인지 확인 (월요일 >= 시작일, 일요일 <= 종료일)
        if current_monday >= start and current_sunday <= end:
            monday_str = current_monday.strftime("%Y-%m-%d")
            sunday_str = current_sunday.strftime("%Y-%m-%d")
            report_date = sunday_str  # 보고서는 해당 주의 일요일 기준
            
            weeks.append((monday_str, sunday_str, report_date))
        
        current_monday += timedelta(days=7)
    
    return weeks

def validate_week_completeness(start_date: str, end_date: str, monday_date: str, sunday_date: str) -> bool:
    """주간 데이터의 완전성 검증"""
    period_start = datetime.strptime(start_date, "%Y-%m-%d")
    period_end = datetime.strptime(end_date, "%Y-%m-%d")
    week_monday = datetime.strptime(monday_date, "%Y-%m-%d")
    week_sunday = datetime.strptime(sunday_date, "%Y-%m-%d")
    
    # 주간 범위가 전체 기간 내에 완전히 포함되는지 확인
    is_complete = (week_monday >= period_start) and (week_sunday <= period_end)
    
    return is_complete

def check_existing_reports(reporter, ticker: str, weeks: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    """이미 생성된 보고서를 확인하고 생성되지 않은 주차만 반환"""
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
        
        # 생성되지 않은 주차만 필터링
        missing_weeks = [
            (monday, sunday, report_date) 
            for monday, sunday, report_date in weeks 
            if report_date not in existing_dates
        ]
        
        print(f"{ticker}: 기존 보고서 {len(existing_dates)}개, 생성할 보고서 {len(missing_weeks)}개")
        return missing_weeks
        
    except Exception as e:
        print(f"{ticker}: 기존 보고서 확인 중 오류: {e}")
        return weeks  # 오류 시 모든 주차 반환

def validate_week_data_availability(ticker: str, monday_date: str, sunday_date: str) -> bool:
    """해당 주차에 충분한 데이터가 있는지 확인"""
    try:
        from src.tools.supabase_data_reader import get_supabase_reader
        reader = get_supabase_reader()
        
        # 해당 주차의 주가 데이터 확인
        response = reader.client.table("stock_prices") \
            .select("time") \
            .eq("ticker", ticker) \
            .gte("time", monday_date) \
            .lte("time", sunday_date + "T23:59:59") \
            .execute()
        
        price_data_count = len(response.data) if response.data else 0
        
        # 최소 3일 이상의 거래일 데이터가 있어야 함
        min_required_days = 3
        has_sufficient_data = price_data_count >= min_required_days
        
        if not has_sufficient_data:
            print(f"  ⚠️  {monday_date}~{sunday_date}: 데이터 부족 ({price_data_count}일)")
        
        return has_sufficient_data
        
    except Exception as e:
        print(f"  ❌ 데이터 검증 오류: {e}")
        return False

def print_week_validation_example():
    """주간 범위 검증 예시 출력"""
    print("\n🧪 주간 범위 검증 예시:")
    print("=" * 50)
    
    test_date = "2023-01-22"  # 일요일
    target = datetime.strptime(test_date, "%Y-%m-%d")
    monday = get_monday_of_week(target)
    sunday = get_sunday_of_week(target)
    
    print(f"보고서 기준일: {test_date} ({target.strftime('%A')})")
    print(f"해당 주 월요일: {monday.strftime('%Y-%m-%d')} ({monday.strftime('%A')})")
    print(f"해당 주 일요일: {sunday.strftime('%Y-%m-%d')} ({sunday.strftime('%A')})")
    print(f"분석 기간: {monday.strftime('%Y-%m-%d')} ~ {sunday.strftime('%Y-%m-%d')}")
    print("=" * 50)

def main():
    """백테스팅 주간 보고서 일괄 생성 (월요일-일요일 기준)"""
    # 설정
    TICKERS = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"]
    START_DATE = "2023-01-01"
    END_DATE = "2025-05-31"
    MODEL_NAME = "solar-pro2-preview"  # 기본 모델
    
    print("🔬 백테스팅 주간 보고서 일괄 생성 시작 (월요일-일요일 기준)")
    print(f"📊 대상 종목: {', '.join(TICKERS)}")
    print(f"📅 기간: {START_DATE} ~ {END_DATE}")
    print("🗓️  주간 단위: 월요일-일요일 (완전한 주만)")
    print(f"🤖 AI 모델: {MODEL_NAME}")
    print("=" * 80)
    
    # 주간 범위 검증 예시 출력
    print_week_validation_example()
    
    # 완전한 주간 단위 생성
    all_weeks = generate_complete_weekly_dates(START_DATE, END_DATE)
    print(f"📋 완전한 주차 수: {len(all_weeks)}개")
    
    if all_weeks:
        print(f"📅 첫 번째 주: {all_weeks[0][0]} (월) ~ {all_weeks[0][1]} (일)")
        print(f"📅 마지막 주: {all_weeks[-1][0]} (월) ~ {all_weeks[-1][1]} (일)")
        
        # 첫 3주와 마지막 3주 예시 출력
        print("\n📝 주간 범위 예시 (처음 3주):")
        for i, (monday, sunday, report_date) in enumerate(all_weeks[:3], 1):
            monday_dt = datetime.strptime(monday, "%Y-%m-%d")
            sunday_dt = datetime.strptime(sunday, "%Y-%m-%d")
            print(f"  {i}주차: {monday} ({monday_dt.strftime('%a')}) ~ {sunday} ({sunday_dt.strftime('%a')}) → 보고서일: {report_date}")
    
    # 보고서 생성기 초기화
    reporter = BacktestingWeeklyReporter(model_name=MODEL_NAME)
    
    # 전체 통계
    total_reports_to_generate = 0
    total_reports_generated = 0
    total_errors = 0
    total_skipped = 0
    
    for ticker in TICKERS:
        print(f"\n📈 {ticker} 종목 보고서 생성 중...")
        print("-" * 60)
        
        # 기존 보고서 확인 및 누락된 주차만 필터링
        missing_weeks = check_existing_reports(reporter, ticker, all_weeks)
        
        if not missing_weeks:
            print(f"✅ {ticker}: 모든 보고서가 이미 생성되어 있습니다.")
            continue
        
        total_reports_to_generate += len(missing_weeks)
        ticker_success = 0
        ticker_errors = 0
        ticker_skipped = 0
        
        # 보고서 생성 루프
        for i, (monday, sunday, report_date) in enumerate(missing_weeks, 1):
            try:
                # 주간 범위 명시적 출력
                monday_dt = datetime.strptime(monday, "%Y-%m-%d")
                sunday_dt = datetime.strptime(sunday, "%Y-%m-%d")
                print(f"[{i}/{len(missing_weeks)}] {ticker} - {monday}({monday_dt.strftime('%a')})~{sunday}({sunday_dt.strftime('%a')}) (보고서일: {report_date})")
                
                # 1. 주차 완전성 검증
                if not validate_week_completeness(START_DATE, END_DATE, monday, sunday):
                    print("  ⚠️  불완전한 주차로 스킵")
                    ticker_skipped += 1
                    total_skipped += 1
                    continue
                
                # 2. 데이터 가용성 검증
                if not validate_week_data_availability(ticker, monday, sunday):
                    print("  ⚠️  데이터 부족으로 스킵")
                    ticker_skipped += 1
                    total_skipped += 1
                    continue
                
                # 3. Solar API Rate Limiting 방지
                if i > 1:
                    wait_time = 3  # 3초 대기
                    print(f"  ⏱️ API Rate Limit 방지를 위해 {wait_time}초 대기...")
                    time.sleep(wait_time)
                
                # 4. 보고서 생성 (weekly_reporter에서 월요일-일요일 범위 자동 계산)
                print(f"  🔄 보고서 생성 중... (분석기간: {monday}~{sunday})")
                report = reporter.generate_weekly_report(ticker, report_date)
                
                # 5. 생성 결과 확인
                if report.startswith("❌"):
                    print(f"  ⚠️  생성 실패: {report[:100]}...")
                    ticker_errors += 1
                    continue
                
                # 6. 보고서 길이 확인 (너무 짧으면 오류로 간주)
                if len(report) < 500:
                    print(f"  ⚠️  보고서가 너무 짧음: ({len(report)} chars)")
                    ticker_errors += 1
                    continue
                
                print(f"  ✅ 완료: {report_date} ({len(report)} chars)")
                ticker_success += 1
                total_reports_generated += 1
                
            except Exception as e:
                print(f"  ❌ 실패: {report_date} - {e}")
                ticker_errors += 1
                total_errors += 1
                
                # 오류 발생 시 추가 대기
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print("  ⏱️ Rate Limit 오류로 인한 추가 대기 (10초)...")
                    time.sleep(10)
                
                continue
        
        print(f"\n📊 {ticker} 결과:")
        print(f"  - 성공: {ticker_success}개")
        print(f"  - 실패: {ticker_errors}개") 
        print(f"  - 스킵: {ticker_skipped}개")
    
    # 최종 통계
    print("\n" + "=" * 80)
    print("🎉 백테스팅 주간 보고서 일괄 생성 완료!")
    print("📊 최종 통계:")
    print(f"  - 총 대상 주차: {len(all_weeks)}개")
    print(f"  - 총 생성 대상: {total_reports_to_generate}개 보고서")
    print(f"  - 성공적으로 생성: {total_reports_generated}개")
    print(f"  - 실패: {total_errors}개")
    print(f"  - 스킵 (불완전/데이터부족): {total_skipped}개")
    print(f"  - 성공률: {(total_reports_generated/total_reports_to_generate)*100:.1f}%" if total_reports_to_generate > 0 else "  - 성공률: N/A")
    
    # 완전한 주차 정보 요약
    if all_weeks:
        print("\n📅 주차 정보:")
        print(f"  - 전체 기간: {START_DATE} ~ {END_DATE}")
        print(f"  - 첫 번째 완전한 주: {all_weeks[0][0]} (월) ~ {all_weeks[0][1]} (일)")
        print(f"  - 마지막 완전한 주: {all_weeks[-1][0]} (월) ~ {all_weeks[-1][1]} (일)")
        print("  - 제외된 불완전 주차: 시작/끝 부분의 부분 주차")
        print("  - 주간 분석 기준: 월요일(시작) ~ 일요일(종료), 보고서일=일요일")
    
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
            print("\n📋 최근 생성된 보고서 (최대 10개):")
            for report in response.data:
                # 해당 보고서의 주차 정보 표시
                report_date = datetime.strptime(report['report_date'], "%Y-%m-%d")
                monday = get_monday_of_week(report_date)
                print(f"  - {report['ticker']}: {report['report_date']} ({monday.strftime('%Y-%m-%d')}~{report['report_date']} 주차)")
        
    except Exception as e:
        print(f"\n⚠️  보고서 요약 조회 실패: {e}")

def test_week_generation():
    """주차 생성 테스트 함수"""
    print("🧪 주차 생성 테스트")
    print("-" * 40)
    
    test_cases = [
        ("2023-01-01", "2023-01-31"),  # 1월 전체
        ("2023-01-15", "2023-02-15"),  # 중간 시작
        ("2023-12-01", "2023-12-31"),  # 12월 전체
    ]
    
    for start, end in test_cases:
        print(f"\n기간: {start} ~ {end}")
        weeks = generate_complete_weekly_dates(start, end)
        
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        
        print(f"시작일 요일: {start_dt.strftime('%A')}")
        print(f"종료일 요일: {end_dt.strftime('%A')}")
        print(f"완전한 주차 수: {len(weeks)}개")
        
        for i, (monday, sunday, report_date) in enumerate(weeks, 1):
            monday_dt = datetime.strptime(monday, "%Y-%m-%d")
            sunday_dt = datetime.strptime(sunday, "%Y-%m-%d")
            print(f"  {i}주차: {monday} ({monday_dt.strftime('%a')}) ~ {sunday} ({sunday_dt.strftime('%a')}) → 보고서: {report_date}")
            print(f"        분석기간: {monday}~{sunday}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_week_generation()
    else:
        main()