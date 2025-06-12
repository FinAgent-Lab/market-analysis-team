"""
공통 주간 보고서 생성 기능
"""
from typing import Dict, Any, List
from abc import ABC, abstractmethod
from langchain_core.language_models.base import BaseLanguageModel

from .data_reader import get_supabase_reader

class BaseWeeklyReporter(ABC):
    """주간 보고서 생성 기본 클래스"""
    
    def __init__(self, llm: BaseLanguageModel):
        self.data_reader = get_supabase_reader()
        self.llm = llm
    
    def generate_weekly_report(self, ticker: str, report_date: str) -> str:
        """주간 보고서 생성 (템플릿 메서드 패턴)"""
        # 1. 데이터 수집
        weekly_data = self.data_reader.get_weekly_data_summary(ticker, report_date)
        print(f"DEBUG: weekly_data keys: {list(weekly_data.keys())}")
        print(f"DEBUG: financial_metrics type: {type(weekly_data.get('financial_metrics'))}")
        print(f"DEBUG: financial_metrics content: {weekly_data.get('financial_metrics')}")
        print(f"DEBUG: report_date_for_financials: {weekly_data.get('report_date_for_financials')}")
        
        # 2. 분석 데이터 생성
        price_analysis = self._analyze_prices(weekly_data.get("prices", []))
        print(f"DEBUG: price_analysis for {ticker} ({report_date}): {price_analysis}")

        news_analysis = self._analyze_news(weekly_data.get("news", []))
        print(f"DEBUG: news_analysis for {ticker} ({report_date}): {news_analysis}")

        insider_analysis = self._analyze_insider_trades(weekly_data.get("insider_trades", []))
        print(f"DEBUG: insider_analysis for {ticker} ({report_date}): {insider_analysis}")
        
        # 3. 보고서 생성 (하위 클래스에서 구현)
        report_params = {
            "ticker": ticker,
            "period": weekly_data.get("period", "N/A"), # 주가/뉴스/내부자거래 기간
            "report_date_original": weekly_data.get("report_date_original", report_date), # 보고서 요청된 기준일 (주로 주의 마지막 날)
            "price_analysis": price_analysis,
            "news_analysis": news_analysis,
            "insider_analysis": insider_analysis,
            "company_facts": weekly_data.get("company_facts", {}),
            "financial_metrics_data": weekly_data.get("financial_metrics", {}),
            "financial_metrics_report_date": weekly_data.get("report_date_for_financials", "N/A")
        }
        
        print(f"DEBUG: report_params financial_metrics_data: {report_params['financial_metrics_data']}")
        print(f"DEBUG: report_params financial_metrics_report_date: {report_params['financial_metrics_report_date']}")
        
        report = self._generate_report(**report_params)
        
        # 4. 보고서 저장 (하위 클래스에서 구현)
        self._save_report(ticker, report_date, report)
        
        return report
    
    @abstractmethod
    def _generate_report(self, **kwargs) -> str:
        """보고서 생성 로직 (하위 클래스에서 구현)"""
        pass
    
    @abstractmethod
    def _save_report(self, ticker: str, report_date: str, content: str) -> bool:
        """보고서 저장 로직 (하위 클래스에서 구현)"""
        pass
    
    # 공통 분석 메서드들
    def _analyze_prices(self, prices: List[Dict]) -> Dict[str, Any]:
        if not prices:
            return {
                "start_price": "N/A", "end_price": "N/A", "high_price": "N/A",
                "low_price": "N/A", "avg_volume": "N/A", "weekly_return": "N/A",
                "volatility": "N/A", "price_data_available": False
            }

        try:
            start_price = prices[0].get('close') # 혹은 'open'
            end_price = prices[-1].get('close')
            
            all_highs = [p.get('high') for p in prices if p.get('high') is not None]
            high_price = max(all_highs) if all_highs else "N/A"
            
            all_lows = [p.get('low') for p in prices if p.get('low') is not None]
            low_price = min(all_lows) if all_lows else "N/A"
            
            total_volume = sum(p.get('volume', 0) for p in prices)
            avg_volume = total_volume / len(prices) if prices else "N/A"
            
            weekly_return = "N/A"
            if isinstance(start_price, (int, float)) and isinstance(end_price, (int, float)) and start_price != 0:
                weekly_return = round(((end_price - start_price) / start_price) * 100, 2)
            
            # 변동성 (일일 종가 기준 수익률의 표준편차) - 단순 예시
            daily_returns = []
            if len(prices) > 1:
                for i in range(1, len(prices)):
                    prev_close = prices[i-1].get('close')
                    curr_close = prices[i].get('close')
                    if isinstance(prev_close, (int, float)) and isinstance(curr_close, (int, float)) and prev_close != 0:
                        daily_returns.append((curr_close - prev_close) / prev_close)
            
            volatility = "N/A"
            if daily_returns:
                import statistics
                volatility = round(statistics.stdev(daily_returns) * 100, 2) # 백분율로 표시

            return {
                "start_price": start_price, "end_price": end_price, "high_price": high_price,
                "low_price": low_price, "avg_volume": round(avg_volume,0) if isinstance(avg_volume, (int,float)) else "N/A",
                "weekly_return": weekly_return, "volatility": volatility,
                "price_data_available": True
            }
        except Exception as e:
            print(f"Error in _analyze_prices: {e}")
            return {
                "start_price": "N/A", "end_price": "N/A", "high_price": "N/A",
                "low_price": "N/A", "avg_volume": "N/A", "weekly_return": "N/A",
                "volatility": "N/A", "price_data_available": False, "error": str(e)
            }
    
    def _analyze_news(self, news: List[Dict]) -> Dict[str, Any]:
        """뉴스 데이터 분석 (공통)"""
        if not news:
            return {"message": "뉴스 데이터가 없습니다."}
        
        # 감정 분석
        positive_news = [n for n in news if n.get("sentiment") == "positive"]
        negative_news = [n for n in news if n.get("sentiment") == "negative"]
        neutral_news = [n for n in news if n.get("sentiment") == "neutral"]
        
        # 일별 뉴스 분포
        news_by_date = {}
        for n in news:
            date = n["date"][:10]  # YYYY-MM-DD만 추출
            if date not in news_by_date:
                news_by_date[date] = 0
            news_by_date[date] += 1
        
        return {
            "total_count": len(news),
            "positive_count": len(positive_news),
            "negative_count": len(negative_news),
            "neutral_count": len(neutral_news),
            "sentiment_ratio": {
                "positive": round(len(positive_news) / len(news) * 100, 1) if news else 0,
                "negative": round(len(negative_news) / len(news) * 100, 1) if news else 0,
                "neutral": round(len(neutral_news) / len(news) * 100, 1) if news else 0
            },
            "daily_distribution": news_by_date,
            "top_headlines": [n["title"] for n in news[:5]]
        }
    
    def _analyze_insider_trades(self, trades: List[Dict]) -> Dict[str, Any]:
        """내부자 거래 분석 (공통)"""
        if not trades:
            return {"message": "내부자 거래 데이터가 없습니다."}
        
        buy_trades = []
        sell_trades = []
        total_buy_value = 0
        total_sell_value = 0
        
        for trade in trades:
            shares = trade.get("transaction_shares")
            value = trade.get("transaction_value", 0) or 0
            
            if shares and float(shares) > 0:
                buy_trades.append(trade)
                total_buy_value += float(value) if value else 0
            elif shares and float(shares) < 0:
                sell_trades.append(trade)
                total_sell_value += abs(float(value)) if value else 0
        
        # 순 거래액 계산
        net_value = total_buy_value - total_sell_value
        
        return {
            "total_trades": len(trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_buy_value": total_buy_value,
            "total_sell_value": total_sell_value,
            "net_value": net_value,
            "net_sentiment": "매수 우세" if net_value > 0 else "매도 우세" if net_value < 0 else "중립",
            "activity_level": "높음" if len(trades) > 10 else "보통" if len(trades) > 5 else "낮음"
        }