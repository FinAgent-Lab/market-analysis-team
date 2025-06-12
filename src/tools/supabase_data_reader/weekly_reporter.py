"""
실시간 주간 보고서 생성
"""
import json
from datetime import datetime
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.base import BaseLanguageModel

from .base_reporter import BaseWeeklyReporter

class WeeklyReportGenerator(BaseWeeklyReporter):
    """실시간 주간 보고서 생성 클래스"""
    
    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        # llm이 제공되지 않으면 기본 모델 사용
        llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        super().__init__(llm)
    
    def _generate_report(self, **kwargs) -> str:
        """실시간 보고서 생성"""
        prompt = ChatPromptTemplate.from_template("""
        다음 데이터를 바탕으로 {ticker}의 주간 보고서를 작성해주세요:
        
        기간: {period}
        주가 분석: {price_analysis}
        뉴스 요약: {news_analysis}
        내부자 거래: {insider_analysis}
        회사 정보: {company_facts}
        
        보고서는 다음 형식으로 작성해주세요:
        
        # {ticker} 주간 보고서 ({period})
        
        ## 📊 주요 지표 요약
        ## 📈 주가 동향 분석  
        ## 📰 주요 뉴스 및 이벤트
        ## 🏢 내부자 거래 활동
        ## 🎯 투자 관점
        ## ⚠️ 리스크 요인
        
        마크다운 형식으로 작성하고, 투자자에게 실용적인 인사이트를 제공해주세요.
        """)
        
        chain = prompt | self.llm
        
        result = chain.invoke({
            "ticker": kwargs["ticker"],
            "period": kwargs["period"],
            "price_analysis": json.dumps(kwargs["price_analysis"], ensure_ascii=False),
            "news_analysis": json.dumps(kwargs["news_analysis"], ensure_ascii=False),
            "insider_analysis": json.dumps(kwargs["insider_analysis"], ensure_ascii=False),
            "company_facts": json.dumps(kwargs["company_facts"], ensure_ascii=False)
        })
        
        return result.content
    
    def _save_report(self, ticker: str, report_date: str, content: str) -> bool:
        """실시간 보고서 저장"""
        try:
            record = {
                "id": f"weekly_report_{ticker}_{report_date}",
                "ticker": ticker,
                "report_date": report_date,
                "report_type": "weekly",
                "content": content,
                "created_at": datetime.now().isoformat()
            }
            
            response = self.data_reader.client.table("stock_reports").upsert(record, on_conflict="id").execute()
            return bool(response.data)
        except Exception as e:
            print(f"보고서 저장 오류: {e}")
            return False