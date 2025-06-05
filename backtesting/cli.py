"""
백테스팅 CLI 도구

명령줄에서 백테스팅 분석을 실행할 수 있는 도구입니다.
"""

import argparse
import sys
import os
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from weekly_reporter import BacktestingWeeklyReporter

def cmd_report(args):
    """단일 보고서 생성"""
    # OpenRouter 모델 지원
    openrouter_models = [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku", 
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "meta-llama/llama-3.1-8b-instruct",
        "google/gemini-pro-1.5"
    ]
    
    model_name = args.model
    if model_name in openrouter_models:
        print(f"🔄 OpenRouter 모델 사용: {model_name}")
    else:
        print(f"🤖 기본 OpenAI 호환 모델 사용: {model_name}")
    
    reporter = BacktestingWeeklyReporter(model_name=model_name)
    
    print(f"🔬 백테스팅 보고서 생성: {args.ticker} ({args.date})")
    
    report = reporter.generate_weekly_report(args.ticker, args.date)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"💾 보고서 저장: {args.output}")
    else:
        print("\n" + report)

def cmd_batch(args):
    """배치 보고서 생성"""
    from weekly_batch_generator import generate_weekly_dates
    
    reporter = BacktestingWeeklyReporter(model_name=args.model)
    tickers = args.tickers.split(",")
    
    dates = generate_weekly_dates(args.start_date, args.end_date)
    
    print(f"🔬 배치 보고서 생성")
    print(f"📊 종목: {', '.join(tickers)}")
    print(f"📅 기간: {args.start_date} ~ {args.end_date}")
    print(f"🔄 간격: 1주")
    print(f"🤖 모델: {args.model}")
    
    for ticker in tickers:
        for date in dates:
            try:
                print(f"생성 중: {ticker} - {date}")
                report = reporter.generate_weekly_report(ticker, date)
                
                if args.output_dir:
                    os.makedirs(f"{args.output_dir}/{ticker}", exist_ok=True)
                    with open(f"{args.output_dir}/{ticker}/report_{date}.md", "w", encoding="utf-8") as f:
                        f.write(report)
                
                print(f"  ✅ 완료")
                
            except Exception as e:
                print(f"  ❌ 실패: {e}")

def cmd_list(args):
    """저장된 보고서 목록 조회"""
    from src.tools.supabase_data_reader import get_supabase_reader
    
    reader = get_supabase_reader()
    
    try:
        query = reader.client.table("stock_reports") \
            .select("ticker, report_date, report_type, created_at") \
            .eq("report_type", "backtesting_weekly") \
            .order("created_at", desc=True)
        
        if args.ticker:
            query = query.eq("ticker", args.ticker)
        
        if args.limit:
            query = query.limit(args.limit)
        
        response = query.execute()
        reports = response.data
        
        if not reports:
            print("📝 저장된 백테스팅 보고서가 없습니다.")
            return
        
        print(f"📋 백테스팅 보고서 목록 (총 {len(reports)}개)")
        print("-" * 60)
        print(f"{'종목':<8} {'보고서날짜':<12} {'생성일시':<20}")
        print("-" * 60)
        
        for report in reports:
            created = report["created_at"][:19].replace("T", " ")
            print(f"{report['ticker']:<8} {report['report_date']:<12} {created:<20}")
            
    except Exception as e:
        print(f"❌ 보고서 목록 조회 실패: {e}")

def cmd_stats(args):
    """백테스팅 보고서 통계 조회"""
    from src.tools.supabase_data_reader import get_supabase_reader
    
    reader = get_supabase_reader()
    
    try:
        # 전체 통계
        response = reader.client.table("stock_reports") \
            .select("ticker, report_date, created_at") \
            .eq("report_type", "backtesting_weekly") \
            .execute()
        
        if not response.data:
            print("📊 생성된 백테스팅 보고서가 없습니다.")
            return
        
        reports = response.data
        total_reports = len(reports)
        
        # 종목별 통계
        ticker_stats = {}
        date_range = {"min": None, "max": None}
        
        for report in reports:
            ticker = report["ticker"]
            report_date = report["report_date"]
            
            if ticker not in ticker_stats:
                ticker_stats[ticker] = 0
            ticker_stats[ticker] += 1
            
            # 날짜 범위 계산
            if date_range["min"] is None or report_date < date_range["min"]:
                date_range["min"] = report_date
            if date_range["max"] is None or report_date > date_range["max"]:
                date_range["max"] = report_date
        
        # 통계 출력
        print("📊 백테스팅 보고서 통계")
        print("=" * 60)
        print(f"📋 총 보고서 수: {total_reports:,}개")
        print(f"📅 날짜 범위: {date_range['min']} ~ {date_range['max']}")
        print(f"📈 종목 수: {len(ticker_stats)}개")
        
        print(f"\n📊 종목별 보고서 수:")
        print("-" * 40)
        for ticker, count in sorted(ticker_stats.items()):
            percentage = (count / total_reports) * 100
            print(f"{ticker:<8}: {count:>4}개 ({percentage:>5.1f}%)")
        
        # 최근 생성된 보고서
        recent_reports = sorted(reports, key=lambda x: x["created_at"], reverse=True)[:5]
        print(f"\n📋 최근 생성된 보고서 (5개):")
        print("-" * 50)
        for report in recent_reports:
            created = report["created_at"][:19].replace("T", " ")
            print(f"{report['ticker']:<8} {report['report_date']:<12} {created}")
        
        # 주별 예상 총 보고서 수 계산
        if date_range["min"] and date_range["max"]:
            start_date = datetime.strptime(date_range["min"], "%Y-%m-%d")
            end_date = datetime.strptime(date_range["max"], "%Y-%m-%d")
            weeks = (end_date - start_date).days // 7 + 1
            expected_total = weeks * len(ticker_stats)
            completion_rate = (total_reports / expected_total) * 100 if expected_total > 0 else 0
            
            print(f"\n📈 완성도 분석:")
            print(f"  - 예상 총 보고서 수: {expected_total:,}개")
            print(f"  - 현재 완성률: {completion_rate:.1f}%")
            
    except Exception as e:
        print(f"❌ 통계 조회 실패: {e}")

def main():
    parser = argparse.ArgumentParser(description="백테스팅 CLI 도구")
    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 명령어")
    
    # 지원 모델 목록
    supported_models = [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "openai/gpt-4o",
        "openai/gpt-4o-mini", 
        "meta-llama/llama-3.1-8b-instruct",
        "google/gemini-pro-1.5"
    ]
    
    # report 명령어
    report_parser = subparsers.add_parser("report", help="단일 보고서 생성")
    report_parser.add_argument("--ticker", required=True, help="종목 심볼")
    report_parser.add_argument("--date", required=True, help="분석 날짜 (YYYY-MM-DD)")
    report_parser.add_argument("--model", default="openai/gpt-4o-mini", 
                              choices=supported_models, help="사용할 LLM 모델")
    report_parser.add_argument("--output", help="출력 파일 경로")
    
    # batch 명령어
    batch_parser = subparsers.add_parser("batch", help="배치 보고서 생성")
    batch_parser.add_argument("--tickers", required=True, help="종목 리스트 (쉼표로 구분)")
    batch_parser.add_argument("--start-date", required=True, help="시작 날짜")
    batch_parser.add_argument("--end-date", required=True, help="종료 날짜")
    batch_parser.add_argument("--model", default="openai/gpt-4o-mini",
                              choices=supported_models, help="사용할 LLM 모델")
    batch_parser.add_argument("--output-dir", help="출력 디렉토리")
    
    # list 명령어
    list_parser = subparsers.add_parser("list", help="저장된 보고서 목록")
    list_parser.add_argument("--ticker", help="특정 종목 필터")
    list_parser.add_argument("--limit", type=int, help="결과 개수 제한")
    
    # stats 명령어 추가
    stats_parser = subparsers.add_parser("stats", help="백테스팅 보고서 통계")
    
    args = parser.parse_args()
    
    if args.command == "report":
        cmd_report(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()
        print(f"\n지원되는 모델:")
        for model in supported_models:
            print(f"  - {model}")

if __name__ == "__main__":
    main()