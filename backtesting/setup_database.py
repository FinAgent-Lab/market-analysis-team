"""
Supabase 데이터베이스 테이블 자동 생성 스크립트
백테스팅 모듈에 필요한 모든 테이블과 인덱스를 생성합니다.
"""

import os
import sys
from dotenv import load_dotenv
from src.tools.supabase_data_reader import get_supabase_reader

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

load_dotenv()


def create_tables():
    """백테스팅에 필요한 모든 테이블 생성"""

    reader = get_supabase_reader()

    # 테이블 생성 SQL들
    table_sqls = [
        # 1. Stock Prices 테이블
        """
        CREATE TABLE IF NOT EXISTS stock_prices (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            time TEXT NOT NULL,
            open DECIMAL NOT NULL,
            close DECIMAL NOT NULL,
            high DECIMAL NOT NULL,
            low DECIMAL NOT NULL,
            volume BIGINT NOT NULL,
            data_type TEXT DEFAULT 'price',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        # 2. Company News 테이블
        """
        CREATE TABLE IF NOT EXISTS company_news (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            source TEXT,
            date TEXT NOT NULL,
            url TEXT NOT NULL,
            sentiment TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        # 3. Financial Metrics 테이블
        """
        CREATE TABLE IF NOT EXISTS financial_metrics (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            report_period TEXT NOT NULL,
            period TEXT NOT NULL,
            currency TEXT,
            market_cap DECIMAL,
            enterprise_value DECIMAL,
            price_to_earnings_ratio DECIMAL,
            price_to_book_ratio DECIMAL,
            price_to_sales_ratio DECIMAL,
            enterprise_value_to_ebitda_ratio DECIMAL,
            enterprise_value_to_revenue_ratio DECIMAL,
            free_cash_flow_yield DECIMAL,
            peg_ratio DECIMAL,
            gross_margin DECIMAL,
            operating_margin DECIMAL,
            net_margin DECIMAL,
            return_on_equity DECIMAL,
            return_on_assets DECIMAL,
            return_on_invested_capital DECIMAL,
            asset_turnover DECIMAL,
            inventory_turnover DECIMAL,
            receivables_turnover DECIMAL,
            days_sales_outstanding DECIMAL,
            operating_cycle DECIMAL,
            working_capital_turnover DECIMAL,
            current_ratio DECIMAL,
            quick_ratio DECIMAL,
            cash_ratio DECIMAL,
            operating_cash_flow_ratio DECIMAL,
            debt_to_equity DECIMAL,
            debt_to_assets DECIMAL,
            interest_coverage DECIMAL,
            revenue_growth DECIMAL,
            earnings_growth DECIMAL,
            book_value_growth DECIMAL,
            earnings_per_share_growth DECIMAL,
            free_cash_flow_growth DECIMAL,
            operating_income_growth DECIMAL,
            ebitda_growth DECIMAL,
            payout_ratio DECIMAL,
            earnings_per_share DECIMAL,
            book_value_per_share DECIMAL,
            free_cash_flow_per_share DECIMAL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        # 4. Insider Trades 테이블
        """
        CREATE TABLE IF NOT EXISTS insider_trades (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            issuer TEXT,
            name TEXT,
            title TEXT,
            is_board_director BOOLEAN,
            transaction_date TEXT,
            transaction_shares DECIMAL,
            transaction_price_per_share DECIMAL,
            transaction_value DECIMAL,
            shares_owned_before_transaction DECIMAL,
            shares_owned_after_transaction DECIMAL,
            security_title TEXT,
            filing_date TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        # 5. Company Facts 테이블
        """
        CREATE TABLE IF NOT EXISTS company_facts (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            name TEXT,
            cik TEXT,
            industry TEXT,
            sector TEXT,
            category TEXT,
            exchange TEXT,
            is_active BOOLEAN,
            listing_date TEXT,
            location TEXT,
            market_cap DECIMAL,
            number_of_employees INTEGER,
            sec_filings_url TEXT,
            sic_code TEXT,
            sic_industry TEXT,
            sic_sector TEXT,
            website_url TEXT,
            weighted_average_shares BIGINT,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        # 6. Stock Reports 테이블 (주간 보고서 저장용)
        """
        CREATE TABLE IF NOT EXISTS stock_reports (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            report_date TEXT NOT NULL,
            report_type TEXT NOT NULL DEFAULT 'weekly',
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
    ]

    # 인덱스 생성 SQL들
    index_sqls = [
        # Stock Prices 인덱스
        "CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker ON stock_prices(ticker);",
        "CREATE INDEX IF NOT EXISTS idx_stock_prices_time ON stock_prices(time);",
        "CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_time ON stock_prices(ticker, time);",
        # Company News 인덱스
        "CREATE INDEX IF NOT EXISTS idx_company_news_ticker ON company_news(ticker);",
        "CREATE INDEX IF NOT EXISTS idx_company_news_date ON company_news(date);",
        "CREATE INDEX IF NOT EXISTS idx_company_news_ticker_date ON company_news(ticker, date);",
        "CREATE INDEX IF NOT EXISTS idx_company_news_url ON company_news(url);",
        # Financial Metrics 인덱스
        "CREATE INDEX IF NOT EXISTS idx_financial_metrics_ticker ON financial_metrics(ticker);",
        "CREATE INDEX IF NOT EXISTS idx_financial_metrics_report_period ON financial_metrics(report_period);",
        "CREATE INDEX IF NOT EXISTS idx_financial_metrics_ticker_period ON financial_metrics(ticker, report_period);",
        # Insider Trades 인덱스
        "CREATE INDEX IF NOT EXISTS idx_insider_trades_ticker ON insider_trades(ticker);",
        "CREATE INDEX IF NOT EXISTS idx_insider_trades_filing_date ON insider_trades(filing_date);",
        "CREATE INDEX IF NOT EXISTS idx_insider_trades_transaction_date ON insider_trades(transaction_date);",
        "CREATE INDEX IF NOT EXISTS idx_insider_trades_ticker_date ON insider_trades(ticker, filing_date);",
        # Company Facts 인덱스
        "CREATE INDEX IF NOT EXISTS idx_company_facts_ticker ON company_facts(ticker);",
        "CREATE INDEX IF NOT EXISTS idx_company_facts_sector ON company_facts(sector);",
        "CREATE INDEX IF NOT EXISTS idx_company_facts_industry ON company_facts(industry);",
        # Stock Reports 인덱스
        "CREATE INDEX IF NOT EXISTS idx_stock_reports_ticker ON stock_reports(ticker);",
        "CREATE INDEX IF NOT EXISTS idx_stock_reports_date ON stock_reports(report_date);",
        "CREATE INDEX IF NOT EXISTS idx_stock_reports_type ON stock_reports(report_type);",
        "CREATE INDEX IF NOT EXISTS idx_stock_reports_ticker_date ON stock_reports(ticker, report_date);",
    ]

    print("🗃️ Supabase 데이터베이스 테이블 생성 시작...")

    # 테이블 생성
    for i, sql in enumerate(table_sqls, 1):
        try:
            reader.client.rpc("execute_sql", {"sql": sql}).execute()
            table_name = sql.split("CREATE TABLE IF NOT EXISTS ")[1].split(" (")[0]
            print(f"  ✅ [{i}/6] {table_name} 테이블 생성 완료")
        except Exception as e:
            table_name = (
                sql.split("CREATE TABLE IF NOT EXISTS ")[1].split(" (")[0]
                if "CREATE TABLE" in sql
                else f"table_{i}"
            )
            print(f"  ❌ [{i}/6] {table_name} 테이블 생성 실패: {e}")

    print("\n📊 인덱스 생성 시작...")

    # 인덱스 생성
    success_count = 0
    for i, sql in enumerate(index_sqls, 1):
        try:
            reader.client.rpc("execute_sql", {"sql": sql}).execute()
            index_name = sql.split("CREATE INDEX IF NOT EXISTS ")[1].split(" ON")[0]
            print(f"  ✅ [{i}/{len(index_sqls)}] {index_name} 인덱스 생성 완료")
            success_count += 1
        except Exception as e:
            index_name = (
                sql.split("CREATE INDEX IF NOT EXISTS ")[1].split(" ON")[0]
                if "CREATE INDEX" in sql
                else f"index_{i}"
            )
            print(f"  ❌ [{i}/{len(index_sqls)}] {index_name} 인덱스 생성 실패: {e}")

    print("\n🎉 데이터베이스 설정 완료!")
    print("   📋 테이블: 6개 생성")
    print(f"   📊 인덱스: {success_count}/{len(index_sqls)}개 생성")
    print("\n📝 다음 단계: uv run backtesting/data_builder.py")


def verify_tables():
    """생성된 테이블들 확인"""
    reader = get_supabase_reader()

    required_tables = [
        "stock_prices",
        "company_news",
        "financial_metrics",
        "insider_trades",
        "company_facts",
        "stock_reports",
    ]

    print("\n🔍 테이블 존재 확인...")

    for table in required_tables:
        try:
            reader.client.table(table).select("*").limit(1).execute()
            print(f"  ✅ {table} - 존재함")
        except Exception as e:
            print(f"  ❌ {table} - 존재하지 않음: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 Supabase 데이터베이스 설정 스크립트")
    print("=" * 50)

    # 환경변수 확인
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ 오류: SUPABASE_URL 또는 SUPABASE_KEY 환경변수가 설정되지 않았습니다.")
        print("💡 .env 파일에 다음을 추가하세요:")
        print("   SUPABASE_URL=https://your-project.supabase.co")
        print("   SUPABASE_KEY=your-service-role-key")
        return

    try:
        # 테이블 생성
        create_tables()

        # 테이블 확인
        verify_tables()

    except Exception as e:
        print(f"❌ 데이터베이스 설정 중 오류 발생: {e}")
        print("\n💡 해결 방법:")
        print("1. Supabase Console에서 SQL Editor로 직접 실행")
        print("2. SUPABASE_KEY가 service_role key인지 확인")
        print("3. 네트워크 연결 상태 확인")


if __name__ == "__main__":
    main()
