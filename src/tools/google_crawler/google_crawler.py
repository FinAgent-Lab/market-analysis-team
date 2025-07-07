import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import random
from typing import Dict, Any, List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_result,
)
from pydantic import BaseModel, ConfigDict, Field


class GoogleCrawlerWrapper(BaseModel):
    """Google News crawler with BeautifulSoup"""
    
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )
    
    headers: Dict[str, str] = Field(
        default_factory=lambda: {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/101.0.4951.54 Safari/537.36"
            )
        }
    )
    
    def is_rate_limited(self, response) -> bool:
        """Check if the response indicates rate limiting (status code 429)"""
        return response.status_code == 429
    
    @retry(
        retry=(retry_if_result(lambda x: x.status_code == 429 if hasattr(x, 'status_code') else False)),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3),
    )
    def make_request(self, url: str) -> requests.Response:
        """Make a request with retry logic for rate limiting"""
        time.sleep(random.uniform(1, 3))
        response = requests.get(url, headers=self.headers, timeout=30)
        return response
    
    def get_news_data(self, query: str, start_date: str, end_date: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape Google News search results for a given query and date range.
        
        Args:
            query: search query
            start_date: start date in the format yyyy-mm-dd or mm/dd/yyyy
            end_date: end date in the format yyyy-mm-dd or mm/dd/yyyy
            max_results: maximum number of results to return
        
        Returns:
            List of news articles with metadata
        """
        try:
            # Convert date format if needed
            if "-" in start_date:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                start_date = start_date_obj.strftime("%m/%d/%Y")
            if "-" in end_date:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                end_date = end_date_obj.strftime("%m/%d/%Y")

            news_results = []
            page = 0
            
            while len(news_results) < max_results and page < 3:
                offset = page * 10
                url = (
                    f"https://www.google.com/search?q={query}"
                    f"&tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}"
                    f"&tbm=nws&start={offset}"
                )

                try:
                    response = self.make_request(url)
                    
                    if response.status_code != 200:
                        print(f"HTTP {response.status_code}: {response.text}")
                        break
                        
                    soup = BeautifulSoup(response.content, "html.parser")
                    results_on_page = soup.select("div.SoaBEf")

                    if not results_on_page:
                        break

                    for el in results_on_page:
                        if len(news_results) >= max_results:
                            break
                            
                        try:
                            link_elem = el.find("a")
                            title_elem = el.select_one("div.MBeuO")
                            snippet_elem = el.select_one(".GI74Re")
                            date_elem = el.select_one(".LfVVr")
                            source_elem = el.select_one(".NUnG9d span")
                            
                            if all([link_elem, title_elem]):
                                link = link_elem.get("href", "")
                                title = title_elem.get_text().strip()
                                snippet = snippet_elem.get_text().strip() if snippet_elem else "No snippet"
                                date = date_elem.get_text().strip() if date_elem else "No date"
                                source = source_elem.get_text().strip() if source_elem else "Unknown source"
                                
                                news_results.append({
                                    "link": link,
                                    "title": title,
                                    "snippet": snippet,
                                    "date": date,
                                    "source": source,
                                    "query": query,
                                    "scraped_at": datetime.now().isoformat()
                                })
                                
                        except Exception as e:
                            print(f"Error processing result: {e}")
                            continue

                    next_link = soup.find("a", id="pnnext")
                    if not next_link:
                        break

                    page += 1

                except Exception as e:
                    print(f"Failed after multiple retries: {e}")
                    break

            return news_results
            
        except Exception as e:
            print(f"Error in get_news_data: {e}")
            return []
    
    def search_with_explicit_dates(self, query: str, **kwargs) -> str:
        """
        Agent-driven search with explicit date parameters
        
        Args:
            query: clean search query (processed by LLM agent)
            **kwargs: start_date, end_date, max_results
        
        Returns:
            Formatted string with search results
        """
        try:
            # Get parameters from agent
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            # Default to last 30 days if not provided
            if not start_date or not end_date:
                end_date_obj = datetime.now()
                start_date_obj = end_date_obj - timedelta(days=30)
                start_date = start_date_obj.strftime("%m/%d/%Y")
                end_date = end_date_obj.strftime("%m/%d/%Y")
            
            max_results = kwargs.get('max_results', 10)
            
            # 디버그 모드에서만 출력 (환경변수로 제어)
            if os.getenv('DEBUG_CRAWLER', 'false').lower() == 'true':
                print("🔍 검색 정보:")
                print(f"  검색 쿼리: '{query}'")
                print(f"  검색 기간: {start_date} ~ {end_date}")
                print(f"  최대 결과: {max_results}")
        
            # Get news data
            results = self.get_news_data(query, start_date, end_date, max_results)
            
            if not results:
                return f"❌ '{query}'에 대한 뉴스 검색 결과를 찾을 수 없습니다. (검색 기간: {start_date} ~ {end_date})"
            
            # Format results
            formatted_results = f"🔍 **Google News 크롤링 결과** ('{query}')\n"
            formatted_results += f"📅 **검색 기간**: {start_date} ~ {end_date}\n"
            formatted_results += f"📊 **검색 결과**: 총 {len(results)}건\n\n"
            
            for i, result in enumerate(results, 1):
                formatted_results += f"**{i}. {result['title']}**\n"
                formatted_results += f"   • 출처: {result['source']}\n"
                formatted_results += f"   • 날짜: {result['date']}\n"
                formatted_results += f"   • 요약: {result['snippet'][:150]}...\n"
                formatted_results += f"   • 링크: {result['link']}\n\n"
            
            return formatted_results
            
        except Exception as e:
            return f"❌ Google News 검색 중 오류 발생: {str(e)}"
