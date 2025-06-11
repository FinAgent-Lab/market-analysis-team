"""
백테스팅 전용 주간 보고서 생성 모듈 (월요일-일요일 기준)
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
from typing import Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.tools.supabase_data_reader.base_reporter import BaseWeeklyReporter

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

load_dotenv()

class SolarChatOpenAI(ChatOpenAI):
    """Solar API 전용 ChatOpenAI 클래스 - Solar API에서 지원하지 않는 파라미터 제거"""
    
    def _get_request_payload(
        self,
        input_: Any,
        *,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> dict:
        """요청 페이로드에서 Solar API에서 지원하지 않는 파라미터 제거"""
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        
        # Solar API에서 지원하지 않는 파라미터들 제거
        solar_unsupported_params = [
            "max_completion_tokens",
            "max_tokens_to_sample", 
            "top_k",
            "repetition_penalty",
            "length_penalty",
            "presence_penalty",
            "frequency_penalty"
        ]
        
        for param in solar_unsupported_params:
            payload.pop(param, None)
        
        return payload

def create_llm(model_name: str = "openai/gpt-4o-mini") -> ChatOpenAI:
    """LLM 인스턴스 생성 (Solar Pro2, OpenRouter, OpenAI 지원)"""
    
    # OpenRouter 모델 목록
    openrouter_models = [
        "openai/gpt-4o-mini",
    ]
    
    # Solar Pro2 모델 사용
    if model_name == "solar-pro2-preview":
        solar_api_key = os.environ.get("SOLAR_API_KEY")
        solar_base_url = "https://api.upstage.ai/v1"
        
        if solar_api_key:
            print(f"☀️ Solar Pro2 사용: {model_name}")
            print("🧠 Solar Pro2 Reasoning 모드 활성화 (high effort)")
            print("⏱️ API Rate Limit 방지를 위해 요청 간격 조정")
            
            # 커스텀 Solar 클래스 사용
            return SolarChatOpenAI(
                model=model_name,
                openai_api_key=solar_api_key,
                openai_api_base=solar_base_url,
                request_timeout=60,
                max_retries=3,
                model_kwargs={
                    "reasoning_effort": "high",
                    "temperature": 0.1,
                    "max_tokens": 4000,
                },
                extra_headers={
                    "User-Agent": "Market Analysis Backtesting"
                }
            )
        else:
            print("❌ SOLAR_API_KEY가 설정되지 않았습니다. OpenAI로 폴백합니다.")
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1
            )
    
    # OpenRouter 모델 사용
    elif model_name in openrouter_models:
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        openrouter_base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        
        if openrouter_api_key:
            print(f"🔄 OpenRouter 사용: {model_name}")
            return ChatOpenAI(
                model=model_name,
                openai_api_key=openrouter_api_key,
                openai_api_base=openrouter_base_url,
                temperature=0.1,
                max_tokens=4000,
                extra_headers={
                    "HTTP-Referer": "https://github.com/your-repo",
                    "X-Title": "Market Analysis Backtesting"
                }
            )
        else:
            print("❌ OPENROUTER_API_KEY가 설정되지 않았습니다. OpenAI로 폴백합니다.")
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1
            )
    
    # OpenAI 모델 사용 (기본값 및 폴백)
    else:
        print(f"🤖 OpenAI 사용: {model_name}")
        return ChatOpenAI(
            model=model_name if model_name.startswith("gpt-") else "gpt-4o-mini",
            temperature=0.1
        )

class BacktestingWeeklyReporter(BaseWeeklyReporter):
    """백테스팅 전용 주간 보고서 생성 클래스 (월요일-일요일 기준)"""
    
    def __init__(self, model_name: str = "solar-pro2-preview"):
        llm = create_llm(model_name)
        super().__init__(llm)
        self.model_name = model_name
        self.supported_tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"]
        self.report_type = "backtesting_weekly"
    
    def get_week_range(self, target_date: str) -> tuple[str, str]:
        """
        주어진 날짜가 속한 주의 월요일-일요일 범위 반환
        
        Args:
            target_date: 주간 보고서 기준일 (보통 일요일)
            
        Returns:
            tuple: (monday_date, sunday_date)
        """
        target = datetime.strptime(target_date, "%Y-%m-%d")
        
        # 해당 주의 월요일 찾기
        days_since_monday = target.weekday()  # 월요일: 0, 화요일: 1, ..., 일요일: 6
        monday = target - timedelta(days=days_since_monday)
        
        # 해당 주의 일요일 찾기
        sunday = monday + timedelta(days=6)
        
        return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")
    
    def safe_get_date_from_item(self, item: dict, date_keys: List[str]) -> Optional[datetime]:
        """데이터 항목에서 안전하게 날짜를 추출"""
        for key in date_keys:
            if key in item and item[key]:
                try:
                    date_str = str(item[key])
                    # 다양한 날짜 형식 처리
                    if 'T' in date_str:
                        # ISO 형식: 2023-01-16T10:30:00
                        return datetime.strptime(date_str[:10], "%Y-%m-%d")
                    else:
                        # 날짜만: 2023-01-16
                        return datetime.strptime(date_str[:10], "%Y-%m-%d")
                except (ValueError, AttributeError) as e:
                    print(f"날짜 파싱 오류 ({key}: {item.get(key)}): {e}")
                    continue
        return None
    
    def collect_weekly_data(self, ticker: str, start_date: str, end_date: str) -> dict:
        """
        월요일-일요일 범위의 주간 데이터 수집
        
        Args:
            ticker: 종목 코드
            start_date: 주 시작일 (월요일)
            end_date: 주 종료일 (일요일)
            
        Returns:
            dict: 수집된 주간 데이터
        """
        try:
            # 기본 데이터 수집 (base_reporter의 data_reader 사용)
            weekly_data = self.data_reader.get_weekly_data_summary(ticker, end_date)
            
            # 월요일-일요일 특화 정보 추가
            if weekly_data:
                # 실제 분석 기간을 월요일-일요일로 수정
                weekly_data['period'] = f"{start_date} ~ {end_date}"
                weekly_data['week_info'] = {
                    'week_start': start_date,
                    'week_end': end_date,
                    'week_type': 'monday_to_sunday',
                    'is_complete_week': True
                }
                
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                
                # 주가 데이터 필터링 (월요일-일요일 범위만)
                if 'prices' in weekly_data and weekly_data['prices']:
                    filtered_prices = []
                    
                    for price in weekly_data['prices']:
                        price_date = self.safe_get_date_from_item(price, ['time', 'date', 'timestamp'])
                        if price_date and start_dt <= price_date <= end_dt:
                            filtered_prices.append(price)
                    
                    weekly_data['prices'] = filtered_prices
                    print(f"📊 주가 데이터 필터링: {len(weekly_data.get('prices', []))} → {len(filtered_prices)}개")
                
                # 뉴스 데이터 필터링 (월요일-일요일 범위만)
                if 'news' in weekly_data and weekly_data['news']:
                    filtered_news = []
                    
                    for news in weekly_data['news']:
                        news_date = self.safe_get_date_from_item(news, ['time', 'date', 'published_at', 'timestamp'])
                        if news_date and start_dt <= news_date <= end_dt:
                            filtered_news.append(news)
                    
                    weekly_data['news'] = filtered_news
                    print(f"📰 뉴스 데이터 필터링: {len(weekly_data.get('news', []))} → {len(filtered_news)}개")
                
                # 내부자 거래 데이터 필터링 (월요일-일요일 범위만)
                if 'insider_trades' in weekly_data and weekly_data['insider_trades']:
                    filtered_insider = []
                    
                    for trade in weekly_data['insider_trades']:
                        trade_date = self.safe_get_date_from_item(trade, ['filing_date', 'transaction_date', 'date'])
                        if trade_date and start_dt <= trade_date <= end_dt:
                            filtered_insider.append(trade)
                    
                    weekly_data['insider_trades'] = filtered_insider
                    print(f"🔄 내부자 거래 필터링: {len(weekly_data.get('insider_trades', []))} → {len(filtered_insider)}개")
            
            return weekly_data
            
        except Exception as e:
            print(f"주간 데이터 수집 오류: {e}")
            import traceback
            print(f"상세 오류: {traceback.format_exc()}")
            return {}
    
    def generate_weekly_report(self, ticker: str, target_date: str) -> str:
        """
        백테스팅용 주간 보고서 생성 (월요일-일요일 기준, 오버라이드)
        
        Args:
            ticker: 종목 코드
            target_date: 보고서 기준일 (해당 주의 일요일)
            
        Returns:
            str: 생성된 보고서 텍스트
        """
        if ticker not in self.supported_tickers:
            return f"❌ 지원되지 않는 종목입니다. 지원 종목: {', '.join(self.supported_tickers)}"
        
        try:
            # 주간 범위 계산 (월요일-일요일)
            monday, sunday = self.get_week_range(target_date)
            
            print(f"📅 주간 범위: {monday} (월) ~ {sunday} (일), 보고서일: {target_date}")
            
            # 주간 데이터 수집
            weekly_data = self.collect_weekly_data(ticker, monday, sunday)
            
            if not weekly_data:
                return f"❌ {ticker} - {target_date}: 주간 데이터 수집 실패"
            
            # 분석 데이터 생성
            price_analysis = self._analyze_prices(weekly_data.get("prices", []))
            news_analysis = self._analyze_news(weekly_data.get("news", []))
            insider_analysis = self._analyze_insider_trades(weekly_data.get("insider_trades", []))
            
            print(f"📈 분석 완료: 주가({len(weekly_data.get('prices', []))}개), 뉴스({len(weekly_data.get('news', []))}개), 내부자({len(weekly_data.get('insider_trades', []))}개)")
            
            # 보고서 생성
            report_params = {
                "ticker": ticker,
                "period": f"{monday} ~ {sunday}",  # 명시적으로 월요일-일요일 기간 설정
                "report_date_original": target_date,
                "price_analysis": price_analysis,
                "news_analysis": news_analysis,
                "insider_analysis": insider_analysis,
                "company_facts": weekly_data.get("company_facts", {}),
                "financial_metrics_data": weekly_data.get("financial_metrics", {}),
                "financial_metrics_report_date": weekly_data.get("report_date_for_financials", "N/A")
            }
            
            report = self._generate_report(**report_params)
            
            if not report or len(report.strip()) < 100:
                return f"❌ {ticker} - {target_date}: 보고서 생성 실패 (내용 부족)"
            
            # Supabase에 저장
            save_success = self.save_report_to_supabase(
                ticker=ticker,
                report_date=target_date,
                report_content=report,
                report_type=self.report_type,
                metadata={
                    "week_start": monday,
                    "week_end": sunday,
                    "week_type": "monday_to_sunday",
                    "analysis_period": f"{monday} ~ {sunday}",
                    "data_counts": {
                        "prices": len(weekly_data.get("prices", [])),
                        "news": len(weekly_data.get("news", [])),
                        "insider_trades": len(weekly_data.get("insider_trades", []))
                    }
                }
            )
            
            if save_success:
                print(f"✅ {ticker} - {target_date}: 보고서 생성 및 저장 완료")
                return report
            else:
                print(f"⚠️ {ticker} - {target_date}: 보고서 생성됨, 저장 실패")
                return report
            
        except Exception as e:
            error_msg = f"❌ {ticker} - {target_date}: 보고서 생성 중 오류 - {e}"
            print(error_msg)
            import traceback
            print(f"상세 오류: {traceback.format_exc()}")
            return error_msg
    
    def save_report_to_supabase(self, ticker: str, report_date: str, report_content: str, 
                               report_type: str, metadata: dict = None) -> bool:
        """Supabase에 보고서 저장"""
        try:
            record = {
                "id": f"{report_type}_{ticker}_{report_date}",
                "ticker": ticker,
                "report_date": report_date,
                "report_type": report_type,
                "content": report_content,
                "metadata": {
                    "purpose": "backtesting",
                    "generated_at": datetime.now().isoformat(),
                    "data_source": "supabase_historical",
                    "analysis_type": "weekly_pattern",
                    "ai_model": self.model_name,
                    **(metadata or {})
                },
                "created_at": datetime.now().isoformat()
            }
            
            response = self.data_reader.client.table("stock_reports").upsert(record, on_conflict="id").execute()
            return bool(response.data)
        except Exception as e:
            print(f"백테스팅 보고서 저장 실패: {e}")
            return False
    
    def _generate_report(self, **kwargs) -> str:
        """백테스팅 보고서 생성"""
        
        # 모델별 시스템 메시지 설정
        if "claude" in self.model_name.lower():
            system_message = "당신은 전문적인 금융 분석가입니다. 제공된 과거 데이터를 기반으로 지정된 형식에 맞춰 상세하고 객관적인 주간 종목 분석 보고서를 작성해주세요."
        elif self.model_name == "solar-pro2-preview":
            system_message = """당신은 전문적인 금융 분석가입니다. Solar Pro2의 고급 추론(Reasoning) 능력을 활용하여 제공된 과거 데이터를 체계적으로 분석해주세요.

분석 접근 방법:
1. 먼저 제공된 모든 데이터를 종합적으로 검토하고 주요 패턴을 식별하세요
2. 주가 움직임, 뉴스 감성, 내부자 거래, 재무 지표 간의 상관관계를 분석하세요  
3. 각 요소가 주식 성과에 미친 영향을 논리적으로 추론하세요
4. 백테스팅 관점에서 해당 주간의 투자 시사점을 도출하세요

지정된 형식에 맞춰 상세하고 객관적인 주간 종목 분석 보고서를 한국어로 작성해주세요."""
        elif "gpt" in self.model_name.lower():
            system_message = "You are a professional financial analyst. Based on the provided historical data, write a detailed and objective weekly stock analysis report in the specified format in Korean."
        else:
            system_message = "당신은 금융 분석 전문가입니다. 과거 데이터를 바탕으로 보고서를 작성합니다."
        
        # kwargs에서 필요한 모든 변수를 미리 추출
        ticker_val = kwargs.get("ticker", "N/A")
        price_news_insider_period_val = kwargs.get("period", "N/A") 
        report_date_original_val = kwargs.get("report_date_original", "N/A") 
        price_analysis_val = kwargs.get("price_analysis", {})
        news_analysis_val = kwargs.get("news_analysis", {})
        insider_analysis_val = kwargs.get("insider_analysis", {})
        company_facts_val = kwargs.get("company_facts", {})
        financial_metrics_data_val = kwargs.get("financial_metrics_data", {})
        financial_metrics_report_date_val = kwargs.get("financial_metrics_report_date", "N/A")

        # 재무 지표 값 추출 (N/A 처리 포함)
        def get_metric(data, key, default="N/A"):
            val = data.get(key)
            return val if val is not None else default

        market_cap_val_str = get_metric(financial_metrics_data_val, "market_cap")
        currency_val_str = financial_metrics_data_val.get("currency", "")
        pe_ratio_val_str = get_metric(financial_metrics_data_val, "price_to_earnings_ratio")
        pb_ratio_val_str = get_metric(financial_metrics_data_val, "price_to_book_ratio")
        ps_ratio_val_str = get_metric(financial_metrics_data_val, "price_to_sales_ratio")
        gross_margin_val_metric = get_metric(financial_metrics_data_val, "gross_margin")
        operating_margin_val_metric = get_metric(financial_metrics_data_val, "operating_margin")
        roe_val_metric = get_metric(financial_metrics_data_val, "return_on_equity")
        debt_to_equity_val_str = get_metric(financial_metrics_data_val, "debt_to_equity")
        revenue_growth_val_metric = get_metric(financial_metrics_data_val, "revenue_growth")
        eps_val_str = get_metric(financial_metrics_data_val, "earnings_per_share")

        def format_percentage(value):
            if isinstance(value, (int, float)):
                return f"{value}%"
            return value

        gross_margin_str_val = format_percentage(gross_margin_val_metric)
        operating_margin_str_val = format_percentage(operating_margin_val_metric)
        roe_str_val = format_percentage(roe_val_metric)
        revenue_growth_str_val = format_percentage(revenue_growth_val_metric)

        # JSON 문자열로 변환
        company_facts_json_str = json.dumps(company_facts_val, ensure_ascii=False, indent=2)
        price_analysis_json_str = json.dumps(price_analysis_val, ensure_ascii=False, indent=2)
        financial_metrics_data_json_str = json.dumps(financial_metrics_data_val, ensure_ascii=False, indent=2)
        news_analysis_json_str = json.dumps(news_analysis_val, ensure_ascii=False, indent=2)
        insider_analysis_json_str = json.dumps(insider_analysis_val, ensure_ascii=False, indent=2)
        
        # 플레이스홀더를 사용한 템플릿 문자열
        prompt_human_template = """
다음 과거 데이터를 바탕으로 {ticker}의 주간 종목 분석 보고서를 작성해주세요. 보고서의 기준일은 {report_date_original}입니다.

**중요: 분석 기간은 반드시 {price_news_insider_period}으로 표시해주세요. 이는 월요일-일요일 기준의 완전한 주간 범위입니다.**

**제공 데이터 요약:**
*   **기업 정보 (Company Facts)**: 회사명 '{company_name}', 산업 '{company_industry}', 섹터 '{company_sector}', 거래소 '{company_exchange}' 등. (세부사항은 아래 전체 데이터 참조)
*   **주간 주가 분석 (Price Analysis)** (기간: {price_news_insider_period}): 주초 시가 {price_start_price}, 주말 종가 {price_end_price}, 주간 수익률 {price_weekly_return}%. (세부사항은 아래 전체 데이터 참조)
*   **주요 재무 지표 (Financial Metrics)** (기준일: {financial_metrics_report_date}): 
    *   시가총액: {market_cap} {currency}
    *   PER: {pe_ratio}, PBR: {pb_ratio}, PSR: {ps_ratio}
    *   매출총이익률: {gross_margin}, 영업이익률: {operating_margin}, ROE: {roe}
    *   부채비율: {debt_to_equity}, 매출 성장률: {revenue_growth}, EPS: {eps}
    *   (세부사항은 아래 전체 데이터 참조)
*   **주간 주요 뉴스 분석 (News Analysis)** (기간: {price_news_insider_period}): 총 {news_total_count}건, 긍정 {news_positive_count}건, 부정 {news_negative_count}건. (세부사항은 아래 전체 데이터 참조)
*   **주간 내부자 거래 분석 (Insider Trades Analysis)** (기간: {price_news_insider_period}): 총 {insider_total_trades}건, 순매수/도: {insider_net_sentiment}. (세부사항은 아래 전체 데이터 참조)

**보고서 형식:**

# {ticker} 주간 종목 분석 보고서 ({report_date_original})

## 1. 기업 개요
*   **회사명**: {company_name}
*   **티커**: {ticker}
*   **산업**: {company_industry}
*   **섹터**: {company_sector}
*   **거래소**: {company_exchange}
*   **주요 사업 요약**: (company_facts의 'description' 필드가 있다면 활용하고, 없다면 name, industry, sector를 바탕으로 AI가 1-2문장으로 간략히 기술)

## 2. 주간 주가 동향 (분석 기간: {price_news_insider_period})
*   **주초 시가**: {price_start_price}
*   **주말 종가**: {price_end_price}
*   **주간 최고가**: {price_high_price}
*   **주간 최저가**: {price_low_price}
*   **주간 평균 거래량**: {price_avg_volume}
*   **주간 수익률**: {price_weekly_return}%
*   **주간 변동성 (일일 수익률 표준편차 기반)**: {price_volatility}%
*   (price_analysis 데이터를 기반으로 AI가 해당 주의 주가 움직임, 주요 변곡점, 거래량 변화 등에 대한 간략한 코멘트를 1-3 문장으로 추가)

## 3. 주요 재무 지표 (최신 데이터 기준일: {financial_metrics_report_date})
*   **시가총액**: {market_cap} {currency}
*   **주가수익비율 (PER)**: {pe_ratio}
*   **주가순자산비율 (PBR)**: {pb_ratio}
*   **주가매출비율 (PSR)**: {ps_ratio}
*   **매출총이익률**: {gross_margin}
*   **영업이익률**: {operating_margin}
*   **자기자본이익률 (ROE)**: {roe}
*   **부채비율 (Debt-to-Equity)**: {debt_to_equity}
*   **매출 성장률 (YoY 또는 TTM 기준)**: {revenue_growth}
*   **주당순이익 (EPS)**: {eps}
*   *(위 지표는 사용 가능한 가장 최신 데이터를 기반으로 합니다. financial_metrics_data가 비어있거나 특정 값이 없을 경우 "N/A" 또는 "데이터 없음"으로 표시해주세요.)*
*   (AI가 위 주요 재무 지표에 대한 간략한 해석을 1-3 문장으로 추가. 예를 들어, PER이 업종 평균 대비 높은지 낮은지, ROE 수준이 양호한지 등. 단, 과거 데이터에 기반한 해석이어야 함.)

## 4. 주간 주요 뉴스 요약 (분석 기간: {price_news_insider_period})
    (news_analysis.top_headlines 와 news_analysis.sentiment_ratio 등을 참고하여 해당 주의 주요 뉴스 2-3개를 요약하고, 각 뉴스의 간략한 내용과 함께 전반적인 뉴스 감성(긍정/부정/중립)을 언급. 뉴스가 없다면 "해당 주 주요 뉴스 없음"으로 표시)
*   **뉴스 요약**: (AI가 news_analysis 데이터를 바탕으로 주요 뉴스 요약 및 감성 분석 결과 기술)

## 5. 주간 내부자 거래 현황 (분석 기간: {price_news_insider_period})
    (insider_analysis 데이터를 참고하여 내부자 거래 요약. 주요 거래(금액 또는 수량 기준)가 있다면 언급하고, 전반적인 순매수/매도 경향(net_sentiment)과 거래 활동 수준(activity_level)을 기술. 거래가 없다면 "해당 주 내부자 거래 없음"으로 표시)
*   **거래 요약**: (AI가 insider_analysis 데이터를 바탕으로 내부자 거래 활동 요약)

## 6. AI 종합 의견 (백테스팅 관점)
*   (AI가 위 1~5번 항목의 Supabase 과거 데이터를 종합하여 해당 주의 종목에 대한 주요 동향, 긍정적/부정적 요인, 주목할 만한 패턴 등을 백테스팅 관점에서 3-5 문장으로 분석 및 요약. 미래 예측이 아닌 과거 데이터에 대한 객관적 해석에 집중할 것.)

---
**보고서 메타데이터**
- 보고서 생성 요청일: {report_date_original}
- 주가/뉴스/내부자거래 분석 기간: {price_news_insider_period}
- 재무 데이터 기준일: {financial_metrics_report_date}
- AI 모델: {ai_model_name}
- 데이터 소스: Supabase 백테스팅 DB
- 분석 목적: 과거 패턴 학습 및 전략 검증 (백테스팅)

**전체 제공 데이터 (참고용):**
*   Company Facts: {company_facts_json}
*   Price Analysis: {price_analysis_json}
*   Financial Metrics Data: {financial_metrics_data_json}
*   News Analysis: {news_analysis_json}
*   Insider Trades Analysis: {insider_analysis_json}

주의: 이 보고서는 과거 데이터를 기반으로 한 백테스팅 분석이며, 실제 투자 조언이 아닙니다.
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", prompt_human_template)
        ])
        
        # chain.invoke에 전달할 변수 딕셔너리 생성
        invoke_params = {
            "ticker": ticker_val,
            "report_date_original": report_date_original_val,
            "company_name": company_facts_val.get('name', 'N/A'),
            "company_industry": company_facts_val.get('industry', 'N/A'),
            "company_sector": company_facts_val.get('sector', 'N/A'),
            "company_exchange": company_facts_val.get('exchange', 'N/A'),
            "price_news_insider_period": price_news_insider_period_val,
            "price_start_price": price_analysis_val.get('start_price', 'N/A'),
            "price_end_price": price_analysis_val.get('end_price', 'N/A'),
            "price_weekly_return": price_analysis_val.get('weekly_return', 'N/A'),
            "price_high_price": price_analysis_val.get('high_price', 'N/A'),
            "price_low_price": price_analysis_val.get('low_price', 'N/A'),
            "price_avg_volume": price_analysis_val.get('avg_volume', 'N/A'),
            "price_volatility": price_analysis_val.get('volatility', 'N/A'),
            "financial_metrics_report_date": financial_metrics_report_date_val,
            "market_cap": market_cap_val_str,
            "currency": currency_val_str,
            "pe_ratio": pe_ratio_val_str,
            "pb_ratio": pb_ratio_val_str,
            "ps_ratio": ps_ratio_val_str,
            "gross_margin": gross_margin_str_val,
            "operating_margin": operating_margin_str_val,
            "roe": roe_str_val,
            "debt_to_equity": debt_to_equity_val_str,
            "revenue_growth": revenue_growth_str_val,
            "eps": eps_val_str,
            "news_total_count": news_analysis_val.get('total_count', 0),
            "news_positive_count": news_analysis_val.get('positive_count', 0),
            "news_negative_count": news_analysis_val.get('negative_count', 0),
            "insider_total_trades": insider_analysis_val.get('total_trades', 0),
            "insider_net_sentiment": insider_analysis_val.get('net_sentiment', 'N/A'),
            "ai_model_name": self.model_name,
            "company_facts_json": company_facts_json_str,
            "price_analysis_json": price_analysis_json_str,
            "financial_metrics_data_json": financial_metrics_data_json_str,
            "news_analysis_json": news_analysis_json_str,
            "insider_analysis_json": insider_analysis_json_str
        }

        try:
            chain = prompt | self.llm
            result = chain.invoke(invoke_params) 
            
            return result.content
            
        except Exception as e:
            error_msg = f"⚠️ 보고서 생성 중 오류 발생: {e}\n\n"
            error_msg += f"🤖 사용된 모델: {self.model_name}\n"
            error_msg += f"📊 종목: {kwargs.get('ticker', 'Unknown')}\n"
            error_msg += f"📅 기간: {kwargs.get('period', 'Unknown')}\n\n"
            error_msg += "입력 데이터 타입 요약:\n"
            error_msg += f"- Company Facts: {type(kwargs.get('company_facts'))}\n"
            error_msg += f"- Price Analysis: {type(kwargs.get('price_analysis'))}\n"
            error_msg += f"- Financial Metrics: {type(kwargs.get('financial_metrics_data'))} (기준일: {kwargs.get('financial_metrics_report_date')})\n"
            error_msg += f"- News Analysis: {type(kwargs.get('news_analysis'))}\n"
            error_msg += f"- Insider Analysis: {type(kwargs.get('insider_analysis'))}\n"
            return error_msg
    
    def _save_report(self, ticker: str, report_date: str, content: str) -> bool:
        """백테스팅 보고서 저장 (base_reporter 호환성을 위한 메서드)"""
        return self.save_report_to_supabase(
            ticker=ticker,
            report_date=report_date,
            report_content=content,
            report_type=self.report_type
        )

def main():
    """백테스팅 주간 보고서 생성 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description="백테스팅 주간 보고서 생성 (월요일-일요일 기준)")
    parser.add_argument("--ticker", required=True, help="종목 심볼 (AAPL, NVDA, MSFT, TSLA, GOOGL)")
    parser.add_argument("--date", required=True, help="보고서 기준일 (YYYY-MM-DD, 보통 일요일)")
    parser.add_argument("--model", default="solar-pro2-preview", help="사용할 LLM 모델 (solar-pro2-preview, openai/gpt-4o-mini 등)")
    
    args = parser.parse_args()
    
    reporter = BacktestingWeeklyReporter(model_name=args.model)
    
    print("🔬 백테스팅 주간 보고서 생성 시작...")
    print(f"📊 종목: {args.ticker}")
    print(f"📅 기준일: {args.date}")
    print(f"🤖 모델: {args.model}")
    
    # 주간 범위 확인
    monday, sunday = reporter.get_week_range(args.date)
    print(f"📅 주간 범위: {monday} (월) ~ {sunday} (일)")
    print("-" * 50)
    
    report = reporter.generate_weekly_report(args.ticker, args.date)
    
    print(report)
    print("\n" + "=" * 50)
    print("✅ 백테스팅 보고서 생성 완료!")

if __name__ == "__main__":
    main()