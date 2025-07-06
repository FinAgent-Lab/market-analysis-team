from typing import Optional
from langchain_core.tools import BaseTool
from pydantic import Field
from src.tools.google_crawler.google_crawler import GoogleCrawlerWrapper


class GoogleCrawlerResults(BaseTool):
    """Google News crawler tool using BeautifulSoup"""
    
    name: str = "google_crawler_results_json"
    description: str = (
        "A news search tool that crawls Google News directly using BeautifulSoup. "
        "Useful for searching recent news articles about stocks, companies, or market trends. "
        "Input should be a search query string with optional date parameters. "
        "Parameters: query (required), start_date (MM/DD/YYYY), end_date (MM/DD/YYYY), max_results (int). "
        "Returns detailed news articles with titles, sources, dates, snippets, and links."
    )
    
    # Pydantic 필드로 선언
    api_wrapper: Optional[GoogleCrawlerWrapper] = Field(default=None, exclude=True)
    init_error: Optional[str] = Field(default=None, exclude=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialize_crawler()
    
    def _initialize_crawler(self):
        """Crawler 초기화"""
        try:
            self.api_wrapper = GoogleCrawlerWrapper()
        except Exception as e:
            self.api_wrapper = None
            self.init_error = str(e)
    
    def _run(
        self, 
        query: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 10,
        **kwargs
    ) -> str:
        """뉴스 크롤링 실행"""
        try:
            # Crawler 초기화 확인
            if self.api_wrapper is None:
                error_msg = getattr(self, 'init_error', 'Unknown error')
                return f"""
❌ **Crawler 초기화 실패**

Google Crawler 초기화 중 오류가 발생했습니다.

**오류 내용:** {error_msg}

**해결 방법:**
1. 네트워크 연결 상태 확인
2. User-Agent 설정 확인
3. 요청 제한 설정 확인

관리자에게 문의하여 크롤러 설정을 확인해주세요.
"""
            
            # 날짜 파라미터를 kwargs에 추가
            search_kwargs = kwargs.copy()
            if start_date:
                search_kwargs['start_date'] = start_date
            if end_date:
                search_kwargs['end_date'] = end_date
            search_kwargs['max_results'] = max_results
            
            # 크롤링을 통한 뉴스 검색 (date_parser 자동 사용 비활성화)
            return self.api_wrapper.search_with_explicit_dates(query, **search_kwargs)
                
        except Exception as e:
            return f"❌ Google News 크롤링 중 오류 발생: {str(e)}"
    
    async def _arun(self, query: str, **kwargs) -> str:
        """비동기 실행 (동기 실행과 동일)"""
        return self._run(query, **kwargs)


class GoogleCrawler(GoogleCrawlerResults):
    """Main Google News crawler tool"""
    
    name: str = "google_crawler"
    description: str = (
        "A news search tool that crawls Google News directly using BeautifulSoup. "
        "Searches for recent news articles about stocks, companies, or market trends. "
        "Parameters: query (required), start_date (MM/DD/YYYY), end_date (MM/DD/YYYY), max_results (int). "
        "If start_date and end_date are not provided, defaults to last 30 days. "
        "Automatically handles rate limiting and returns formatted news results."
    )


# 하위 호환성을 위한 팩토리 함수
def create_google_crawler_tool() -> GoogleCrawler:
    """GoogleCrawler 인스턴스를 생성하여 반환"""
    return GoogleCrawler()
