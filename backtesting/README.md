# Market Analysis Team - Backtesting Module

이 모듈은 과거 주식 데이터를 활용한 백테스팅 분석 및 주간 보고서 자동 생성을 위한 도구들을 제공합니다.

## 📁 디렉토리 구조

```
backtesting/
├── data_builder.py              # 백테스팅용 데이터 수집 및 구축
├── weekly_reporter.py           # 주간 보고서 생성기 (월-일 기준)
├── weekly_batch_generator.py    # 대량 주간 보고서 일괄 생성 (메인)
├── run_full_pipeline.py         # 전체 파이프라인 실행기 (선택사항)
├── setup_database.py            # Supabase 데이터베이스 테이블 생성
└── README.md                    # 사용 가이드
```

## 🚀 사용법

### 0. 데이터베이스 설정 (최초 1회)

#### 방법 1: SQL 직접 실행 (권장)

Supabase Console에서 SQL Editor를 열고 다음 SQL을 실행하세요:

```sql
-- 모든 테이블을 한 번에 생성하는 SQL
-- SQL Editor에 복사 후 RUN 클릭

-- 1. Stock Prices 테이블
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

-- 2. Company News 테이블
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

-- 3. Financial Metrics 테이블
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

-- 4. Insider Trades 테이블
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

-- 5. Company Facts 테이블
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

-- 6. Stock Reports 테이블 (주간 보고서 저장용)
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

-- 성능 최적화를 위한 인덱스들
-- Stock Prices 인덱스
CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker ON stock_prices(ticker);
CREATE INDEX IF NOT EXISTS idx_stock_prices_time ON stock_prices(time);
CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_time ON stock_prices(ticker, time);

-- Company News 인덱스
CREATE INDEX IF NOT EXISTS idx_company_news_ticker ON company_news(ticker);
CREATE INDEX IF NOT EXISTS idx_company_news_date ON company_news(date);
CREATE INDEX IF NOT EXISTS idx_company_news_ticker_date ON company_news(ticker, date);
CREATE INDEX IF NOT EXISTS idx_company_news_url ON company_news(url);

-- Financial Metrics 인덱스
CREATE INDEX IF NOT EXISTS idx_financial_metrics_ticker ON financial_metrics(ticker);
CREATE INDEX IF NOT EXISTS idx_financial_metrics_report_period ON financial_metrics(report_period);
CREATE INDEX IF NOT EXISTS idx_financial_metrics_ticker_period ON financial_metrics(ticker, report_period);

-- Insider Trades 인덱스
CREATE INDEX IF NOT EXISTS idx_insider_trades_ticker ON insider_trades(ticker);
CREATE INDEX IF NOT EXISTS idx_insider_trades_filing_date ON insider_trades(filing_date);
CREATE INDEX IF NOT EXISTS idx_insider_trades_transaction_date ON insider_trades(transaction_date);
CREATE INDEX IF NOT EXISTS idx_insider_trades_ticker_date ON insider_trades(ticker, filing_date);

-- Company Facts 인덱스
CREATE INDEX IF NOT EXISTS idx_company_facts_ticker ON company_facts(ticker);
CREATE INDEX IF NOT EXISTS idx_company_facts_sector ON company_facts(sector);
CREATE INDEX IF NOT EXISTS idx_company_facts_industry ON company_facts(industry);

-- Stock Reports 인덱스
CREATE INDEX IF NOT EXISTS idx_stock_reports_ticker ON stock_reports(ticker);
CREATE INDEX IF NOT EXISTS idx_stock_reports_date ON stock_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_stock_reports_type ON stock_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_stock_reports_ticker_date ON stock_reports(ticker, report_date);
```

#### 방법 2: Python 스크립트 실행

```bash
# Python으로 테이블 자동 생성
uv run backtesting/setup_database.py
```

### 1. 환경 설정

```bash
# 환경변수 설정 (.env 파일)
SOLAR_API_KEY=your_solar_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
FINANCIAL_DATASETS_API_KEY=your_financial_datasets_api_key
```

### 2. 데이터 수집 (필수 - 최초 1회)

```bash
# 백테스팅용 과거 데이터 수집 및 구축
uv run backtesting/data_builder.py
```

**수집 데이터:**
- **대상 종목**: AAPL, NVDA, MSFT, TSLA, GOOGL
- **기간**: 2023-01-01 ~ 2025-05-31
- **데이터 유형**: 주가, 뉴스, 내부자 거래, 재무 지표, 기업 정보

## 🗃️ 데이터베이스 구조

### 주요 테이블들

| 테이블명 | 용도 | 주요 컬럼 |
|---------|------|----------|
| `stock_prices` | 주가 데이터 | ticker, time, open, close, high, low, volume |
| `company_news` | 뉴스 데이터 | ticker, title, date, url, sentiment |
| `financial_metrics` | 재무 지표 | ticker, report_period, PER, PBR, ROE 등 |
| `insider_trades` | 내부자 거래 | ticker, filing_date, transaction_value 등 |
| `company_facts` | 기업 정보 | ticker, name, sector, industry, market_cap |
| `stock_reports` | 생성된 보고서 | ticker, report_date, content, metadata |

### 백테스팅 보고서 저장
- **테이블**: `stock_reports`
- **보고서 타입**: `backtesting_weekly`
- **ID 형식**: `backtesting_weekly_{TICKER}_{YYYY-MM-DD}`
- **메타데이터**: 생성 시간, AI 모델, 데이터 소스 등

## 📋 실행 예시

### 🎯 완전한 설정 및 실행 순서

```bash
# 0. 프로젝트 루트에서 실행
cd ~/pseudo-co/market-analysis-team

# 1. 데이터베이스 테이블 생성 (최초 1회)
# 방법 1: Supabase Console에서 SQL 실행 (권장)
# 방법 2: Python 스크립트 실행
uv run backtesting/setup_database.py

# 2. 데이터 수집 (최초 1회, 약 1-2시간 소요)
uv run backtesting/data_builder.py

# 3. 단일 보고서 테스트 (선택사항)
uv run backtesting/weekly_reporter.py --ticker AAPL --date 2023-03-19

# 4. 전체 보고서 생성 (약 4-5시간 소요)
uv run backtesting/weekly_batch_generator.py

# 5. 결과 확인
# Supabase Console → stock_reports 테이블
# 조건: report_type = 'backtesting_weekly'
```

### 📊 예상 실행 시간
- **데이터베이스 설정**: 1-2분
- **데이터 수집**: 1시간 이내 (종목별 약 10-20분)
- **전체 보고서 생성**: 4-5시간
- **단일 보고서**: 10-30초 (API 응답 시간에 따라)

## 🔍 트러블슈팅

### 데이터베이스 관련

#### 🗃️ 테이블 생성 관련
```bash
# 문제: 테이블이 이미 존재함
해결: IF NOT EXISTS 사용으로 안전하게 처리됨

# 문제: 권한 부족
확인: Supabase 프로젝트의 SQL Editor 권한
확인: SUPABASE_KEY가 service_role key인지 확인

# 문제: 연결 오류
확인: SUPABASE_URL 형식 (https://xxx.supabase.co)
확인: 네트워크 연결 상태
```

## 🛠️ 데이터베이스 유지보수

### 테이블 상태 확인
```sql
-- 테이블 존재 확인
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 각 테이블의 레코드 수 확인
SELECT 
    (SELECT COUNT(*) FROM stock_prices) as stock_prices_count,
    (SELECT COUNT(*) FROM company_news) as company_news_count,
    (SELECT COUNT(*) FROM financial_metrics) as financial_metrics_count,
    (SELECT COUNT(*) FROM insider_trades) as insider_trades_count,
    (SELECT COUNT(*) FROM company_facts) as company_facts_count,
    (SELECT COUNT(*) FROM stock_reports) as stock_reports_count;
```

### 보고서 현황 확인
```sql
-- 생성된 보고서 현황
SELECT 
    ticker,
    COUNT(*) as report_count,
    MIN(report_date) as first_report,
    MAX(report_date) as last_report
FROM stock_reports 
WHERE report_type = 'backtesting_weekly'
GROUP BY ticker
ORDER BY ticker;
```

## 📈 확장 가능성

### 🎯 단기 확장
- **추가 종목**: `TICKERS` 리스트에 종목 추가
- **기간 조정**: `START_DATE`, `END_DATE` 수정
- **모델 변경**: OpenAI, Anthropic 모델로 전환 가능

### 🚀 장기 확장
- **다양한 분석 주기**: 일간, 월간, 분기간 보고서
- **추가 데이터 소스**: 옵션, 선물, 크립토 데이터
- **고급 분석**: 기술적 지표, 퀀트 분석
- **시각화**: 차트, 그래프 자동 생성
- **알림 시스템**: Slack, 이메일 알림 연동

### 🔧 커스터마이징
- **보고서 형식**: 템플릿 수정으로 출력 형식 변경
- **분석 깊이**: 프롬프트 엔지니어링으로 분석 수준 조정
- **성과 지표**: 추가 KPI 및 벤치마크 분석

---

## 🎉 마무리

이 백테스팅 모듈을 통해 **과거 주식 데이터를 체계적으로 분석**하고, **AI 기반의 통찰력 있는 주간 보고서**를 자동 생성할 수 있습니다. 

**Solar Pro2의 고급 추론 능력**을 활용하여 단순한 데이터 요약을 넘어선 **깊이 있는 금융 분석**을 제공합니다.

**시작하기**: 
1. 데이터베이스 테이블 생성 (SQL 또는 Python)
2. `uv run backtesting/data_builder.py` 
3. `uv run backtesting/weekly_batch_generator.py`

