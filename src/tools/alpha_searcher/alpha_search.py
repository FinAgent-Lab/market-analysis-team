import requests
import time
import random
import json
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import cloudscraper
from requests_html import HTMLSession
import aiohttp
import asyncio
from typing import ClassVar, List
from pydantic import BaseModel, Field, ConfigDict

# class AlphaSearch(BaseModel):
#     """Input for the Alpha Search tool."""

#     query: str = Field(description="search query to look up")


# description = '''
# This is a code that crawls alpha site research data and urls.
# '''

class AlphaSearchWrapper(BaseModel):

    headers: ClassVar[dict] = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'TE': 'Trailers'
    }
    
        
    proxies: ClassVar[List[str]] = [
        'http://123.456.789.10:8080',
        'http://98.765.432.10:3128'
    ]
    
    scraper: ClassVar[cloudscraper.CloudScraper] = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            delay=10
        )
    session: ClassVar[HTMLSession] = HTMLSession()
    
    model_config: ConfigDict = ConfigDict(
        extra="forbid",
    )
    
    ticker: str = "AAPL"
    search_type: str = "report"
    
    def random_delay(self, min_seconds=1, max_seconds=5):
        """무작위 지연 시간 생성"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def get_random_proxy(self):
        """무작위 프록시 선택"""
        return random.choice(self.proxies) if self.proxies else None
    
    def get_random_headers(self):
        """무작위 헤더 생성"""
        headers = self.headers.copy()
        headers['User-Agent'] = self.ua.random
        return headers
    
    def method1_basic_requests(self, url):
        """기본 requests 라이브러리 + 개선된 헤더와 쿠키 관리"""
        try:
            headers = self.get_random_headers()
            
            session = requests.Session()
            
            favicon_url = url.split('/')[0] + '//' + url.split('/')[2] + '/favicon.ico'
            session.get(favicon_url, headers=headers, timeout=10)
            
            response = session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"Method 1 failed: Status code {response.status_code}")
                return None
        except Exception as e:
            print(f"Method 1 error: {e}")
            return None
    
    def method2_cloudscraper(self, url):
        """CloudScraper 사용 (Cloudflare 보호 우회)"""
        try:
            self.scraper.headers.update(self.get_random_headers())
            
            response = self.scraper.get(url, timeout=15)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"Method 2 failed: Status code {response.status_code}")
                return None
        except Exception as e:
            print(f"Method 2 error: {e}")
            return None
    
    def method3_requests_html(self, url):
        """Requests-HTML 사용 (JavaScript 렌더링)"""
        try:
            self.session.headers.update(self.get_random_headers())
            
            response = self.session.get(url, timeout=15)
            
            response.html.render(sleep=3, timeout=20)
            
            if response.status_code == 200:
                return response.html.html
            else:
                print(f"Method 3 failed: Status code {response.status_code}")
                return None
        except Exception as e:
            print(f"Method 3 error: {e}")
            return None
    
    def method4_proxy_rotation(self, url):
        """프록시 서버 로테이션"""
        try:
            proxy = self.get_random_proxy()
            if not proxy:
                print("No proxies available")
                return None
                
            proxies = {
                'http': proxy,
                'https': proxy,
            }
            
            headers = self.get_random_headers()
            
            response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"Method 4 failed: Status code {response.status_code}")
                return None
        except Exception as e:
            print(f"Method 4 error: {e}")
            return None
    
    async def method5_async_requests(self, urls):
        """비동기 요청 (여러 URL 크롤링 시 효율적)"""
        results = {}
        
        async def fetch_url(session, url):
            try:
                headers = self.get_random_headers()
                
                await asyncio.sleep(random.uniform(1, 3))
                
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        return url, html
                    else:
                        print(f"Async request failed for {url}: Status code {response.status}")
                        return url, None
            except Exception as e:
                print(f"Async error for {url}: {e}")
                return url, None
        
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_url(session, url) for url in urls]
            responses = await asyncio.gather(*tasks)
            
            for url, html in responses:
                results[url] = html
                
        return results
    
    def method6_api_scraping(self, url, api_endpoint=None):
        """API 활용 (많은 사이트가 내부 API 사용)"""
        try:
            session = requests.Session()
            headers = self.get_random_headers()
            
            initial_response = session.get(url, headers=headers, timeout=10)
            
            if not api_endpoint:
                soup = BeautifulSoup(initial_response.text, 'html.parser')
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'apiUrl' in script.string:
                        # 정규식으로 API URL 추출
                        import re
                        match = re.search(r'apiUrl\s*:\s*[\'"]([^\'"]+)[\'"]', script.string)
                        if match:
                            api_endpoint = match.group(1)
                            break
            
            if not api_endpoint:
                print("Could not find API endpoint")
                return None
            
            params = {
                'symbol': 'AAPL',  # 티커
                'period': '1M',    # 기간
                'type': 'analysis' # 데이터 유형
            }
            
            # API 요청
            api_url = f"{api_endpoint}?{urlencode(params)}"
            api_response = session.get(api_url, headers=headers)
            
            if api_response.status_code == 200:
                return api_response.json()  # JSON 데이터 반환
            else:
                print(f"API request failed: Status code {api_response.status_code}")
                return None
        except Exception as e:
            print(f"API scraping error: {e}")
            return None
    
    def method7_query_parameter_variation(self, base_url):
        """쿼리 파라미터 변형"""
        try:
            params_variations = [
                {'v': '1', 'source': 'web'},
                {'version': '2', 'client': 'browser'},
                {'mode': 'desktop', 'app': 'false'},
                {'mobile': 'false', 'direct': 'true'},
                {}  
            ]
            
            
            for params in params_variations:
                url = f"{base_url}?{urlencode(params)}" if params else base_url
                headers = self.get_random_headers()
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    return response.text
                
                self.random_delay(2, 5)
            
            print("All query parameter variations failed")
            return None
        except Exception as e:
            print(f"Query parameter variation error: {e}")
            return None
    
    def get_stock_data(self, ticker, method="all"):
        """특정 기업의 주식 데이터를 다양한 방법으로 크롤링"""
        # 다양한 소스 URL
        urls = {
            "seeking_alpha": f"https://seekingalpha.com/symbol/{ticker}/analysis",
            # "yahoo_finance": f"https://finance.yahoo.com/quote/{ticker}/analysis",
            # "finviz": f"https://finviz.com/quote.ashx?t={ticker}",
            # "marketwatch": f"https://www.marketwatch.com/investing/stock/{ticker}/analystestimates",
            # "tipranks": f"https://www.tipranks.com/stocks/{ticker.lower()}/forecast",
            # "zacks": f"https://www.zacks.com/stock/quote/{ticker}"
        }
        
        results = {}
        
        for source, url in urls.items():
            print(f"크롤링 중: {source} for {ticker}")
            
            # 과도한 요청 방지를 위한 대기
            self.random_delay(3, 7)
            
            if method == "all" or method == "basic":
                html = self.method1_basic_requests(url)
                if html:
                    results[source] = {"method": "basic", "data": html}
                    continue
            
            if method == "all" or method == "cloudscraper":
                html = self.method2_cloudscraper(url)
                if html:
                    results[source] = {"method": "cloudscraper", "data": html}
                    continue
            
            if method == "all" or method == "requests_html":
                html = self.method3_requests_html(url)
                if html:
                    results[source] = {"method": "requests_html", "data": html}
                    continue
            
            if method == "all" or method == "proxy":
                html = self.method4_proxy_rotation(url)
                if html:
                    results[source] = {"method": "proxy", "data": html}
                    continue
            
            if method == "all" or method == "params":
                html = self.method7_query_parameter_variation(url)
                if html:
                    results[source] = {"method": "params", "data": html}
                    continue
            
            # API 스크래핑은 사이트별로 다르므로 구현 생략
        
        return results
    
    def parse_stock_data(self, results):
        """크롤링한 데이터 파싱"""
        parsed_data = {}
        
        for source, result in results.items():
            html = result["data"]
            soup = BeautifulSoup(html, 'html.parser')
            
            if source == "seeking_alpha":
                # 예: Seeking Alpha 데이터 파싱
                articles = soup.find_all('article')
                parsed_data[source] = []
                
                for article in articles:
                    try:
                        title_elem = article.find('a', attrs={'data-test-id': 'post-list-item-title'})
                        if not title_elem:
                            continue
                            
                        title = title_elem.text.strip()
                        link = "https://seekingalpha.com" + title_elem['href']
                        
                        date_elem = article.find('span', attrs={'data-test-id': 'post-list-date'})
                        date = date_elem.text.strip() if date_elem else "N/A"
                        
                        parsed_data[source].append({
                            'title': title,
                            'link': link,
                            'date': date
                        })
                    except Exception as e:
                        print(f"파싱 오류 (Seeking Alpha): {e}")
            
            elif source == "yahoo_finance":
                # 예: Yahoo Finance 데이터 파싱
                analyst_section = soup.find('section', attrs={'data-test': 'qsp-analyst'})
                parsed_data[source] = {}
                
                if analyst_section:
                    tables = analyst_section.find_all('table')
                    for i, table in enumerate(tables):
                        rows = table.find_all('tr')
                        table_data = []
                        
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            row_data = [cell.text.strip() for cell in cells]
                            if row_data:
                                table_data.append(row_data)
                        
                        parsed_data[source][f'table_{i+1}'] = table_data
            
            # 다른 소스들에 대한 파싱 로직도 구현해야 함
            
        return parsed_data
    def crawl_seeking_alpha_articles_full(self, article_links, method="all"):
        """Seeking Alpha 기사의 전체 콘텐츠를 크롤링하는 함수"""
        article_contents = {}
        
        for i, article_info in enumerate(article_links):
            title = article_info['title']
            link = article_info['link']
            
            print(f"크롤링 중 ({i+1}/{len(article_links)}): {title}")
            
            self.random_delay(3, 7)
            
            try:
                session = HTMLSession()
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Referer': 'https://seekingalpha.com/',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Cache-Control': 'max-age=0',
                }
                
                session.headers.update(headers)
                
                response = session.get(link, timeout=30)
                
                scrolls = [
                    'window.scrollTo(0, document.body.scrollHeight * 0.3);',
                    'window.scrollTo(0, document.body.scrollHeight * 0.6);',
                    'window.scrollTo(0, document.body.scrollHeight);',
                    'window.scrollTo(0, document.body.scrollHeight * 1.5);' # 일부 사이트는 더 긴 스크롤이 필요함
                ]
                
                response.html.render(sleep=5, timeout=60, script="\n".join(scrolls), keep_page=True)
                
                try:
                    for selector in ['button:contains("Read More")', 'button:contains("Continue Reading")', 
                                    'a:contains("Read Full Article")', '.read-more-button', 
                                    '[data-test-id="read-more-button"]']:
                        try:
                            response.html.render(script=f"""
                                (function() {{
                                    const readMoreBtn = document.querySelector('{selector}');
                                    if (readMoreBtn) {{
                                        readMoreBtn.click();
                                        return true;
                                    }}
                                    return false;
                                }})();
                            """, reload=False, sleep=3)
                        except Exception as e:
                            continue
                except Exception as e:
                    print(f"버튼 클릭 시도 중 오류: {e}")
                
                try:
                    response.html.render(script="""
                        (function() {
                            // 로그인 모달, 페이월 요소 제거
                            const modals = document.querySelectorAll('[id*="modal"], [class*="modal"], [id*="paywall"], [class*="paywall"]');
                            modals.forEach(el => el.remove());
                            
                            // 배경 스크롤 활성화
                            document.body.style.overflow = 'auto';
                            
                            // blur 효과가 있는 요소 복구
                            document.querySelectorAll('[class*="blur"]').forEach(el => {
                                el.style.filter = 'none';
                                el.style.textShadow = 'none';
                                el.style.color = 'black';
                            });
                            
                            // 숨겨진 콘텐츠 표시
                            document.querySelectorAll('[class*="hidden"], [style*="display: none"]').forEach(el => {
                                // 실제 콘텐츠인지 확인 (문단, 제목 등)
                                if (el.tagName === 'P' || el.tagName === 'DIV' || el.tagName === 'SECTION' || 
                                    el.tagName === 'ARTICLE' || el.tagName.startsWith('H')) {
                                    el.style.display = 'block';
                                }
                            });
                        })();
                    """, reload=False, sleep=2)
                except Exception as e:
                    print(f"모달 제거 시도 중 오류: {e}")
                
                html = response.html.html
                
                try:
                    response.html.close()
                except:
                    pass
                
                soup = BeautifulSoup(html, 'html.parser')
                
                article_container = None
                selectors = [
                    'div[data-test-id="content-container"]',
                    'article',
                    'div.article-content',
                    'div.paywall-content',
                    'div.article__content',
                    'div[id*="article-content"]',
                    'section.article-body',
                    'div.sa-art'  # Seeking Alpha 특화 선택자
                ]
                
                for selector in selectors:
                    container = soup.select_one(selector)
                    if container and len(container.text.strip()) > 200:  # 최소 콘텐츠 길이 확인
                        article_container = container
                        break
                
                
                if not article_container:
                    divs = soup.find_all('div')
                    article_divs = []
                    
                    for div in divs:
                        if len(div.text.strip()) > 500:  # 충분히 긴 텍스트 블록
                            article_divs.append((div, len(div.text.strip())))
                    
                    if article_divs:
                        article_divs.sort(key=lambda x: x[1], reverse=True)
                        article_container = article_divs[0][0]
                
                content = ""
                
                if article_container:
                    title_element = soup.find('h1')
                    title_text = title_element.text.strip() if title_element else title
                    
                    author = soup.select_one('[data-test-id="author-name"], .author-name, [rel="author"]')
                    author_text = author.text.strip() if author else "Unknown"
                    
                    date = soup.select_one('time, [data-test-id="published-on"], .publication-date')
                    date_text = date.text.strip() if date else "Unknown"
                    
                    paragraphs = article_container.find_all(['p', 'h2', 'h3', 'h4', 'blockquote', 'ul', 'ol'])
                    
                    for element in paragraphs:
                        if any(x in str(element.get('class', '')).lower() for x in ['ad', 'promo', 'related', 'newsletter']):
                            continue
                        
                        if element.name in ['h2', 'h3', 'h4']:
                            content += f"\n## {element.text.strip()}\n\n"
                        elif element.name == 'blockquote':
                            content += f"\n> {element.text.strip()}\n\n"
                        elif element.name in ['ul', 'ol']:
                            for li in element.find_all('li'):
                                content += f"• {li.text.strip()}\n"
                            content += "\n"
                        else:
                            if len(element.text.strip()) > 0:
                                content += f"{element.text.strip()}\n\n"
                    
                    tables = article_container.find_all('table')
                    table_data = []
                    
                    for table in tables:
                        rows = table.find_all('tr')
                        t_data = []
                        
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            row_data = [cell.text.strip() for cell in cells]
                            if row_data:
                                t_data.append(row_data)
                        
                        if t_data:
                            content += "\n**Table:**\n"
                            for row in t_data:
                                content += " | ".join(row) + "\n"
                            content += "\n"
                            
                            table_data.append(t_data)
                    
                    article_data = {
                        'title': title_text,
                        'author': author_text,
                        'date': date_text,
                        'content': content,
                        'url': link,
                        'tables': table_data,
                        'content_length': len(content)
                    }
                    
                    if len(content) < 500:
                        article_data['warning'] = "Content may be incomplete - length is suspiciously short"
                    
                    article_contents[title] = article_data
                    
                else:
                    article_contents[title] = {
                        'error': 'Could not identify article content container',
                        'url': link,
                        'html_length': len(html)
                    }
                    
            except Exception as e:
                print(f"크롤링 중 오류 발생: {str(e)}")
                article_contents[title] = {
                    'error': f'Error during crawling: {str(e)}',
                    'url': link
                }
        
        return article_contents
    def crawl_seeking_alpha_articles(self, article_links, method="all"):
        """Seeking Alpha 기사 URL들의 내용을 크롤링하는 개선된 함수"""
        article_contents = {}
        
        for i, article_info in enumerate(article_links):
            title = article_info['title']
            link = article_info['link']
            
            print(f"크롤링 중: {title} ({i+1}/{len(article_links)})")
            
            self.random_delay(3, 7)
            
            html = None
            method_used = None
            
            if method == "all" or method == "requests_html":
                html = self.method3_requests_html(link)
                if html:
                    method_used = "requests_html"
                # import pdb;pdb.set_trace()
            if (not html) and (method == "all" or method == "cloudscraper"):
                html = self.method2_cloudscraper(link)
                if html:
                    method_used = "cloudscraper"
                # import pdb;pdb.set_trace()
            if (not html) and (method == "all" or method == "basic"):
                html = self.method1_basic_requests(link)
                if html:
                    method_used = "basic"
                # import pdb;pdb.set_trace()
            if (not html) and (method == "all" or method == "proxy"):
                html = self.method4_proxy_rotation(link)
                if html:
                    method_used = "proxy"
                # import pdb;pdb.set_trace()
            if (not html) and (method == "all" or method == "params"):
                html = self.method7_query_parameter_variation(link)
                if html:
                    method_used = "params"
                # import pdb;pdb.set_trace()
                
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                
                try:
                    actual_title = soup.find('h1', attrs={'data-test-id': 'article-title'})
                    if not actual_title:
                        actual_title = soup.find('h1')  # 백업 방법
                    actual_title = actual_title.text.strip() if actual_title else title
                    
                    author = soup.find('span', attrs={'data-test-id': 'author-name'})
                    if not author:
                        author = soup.find('a', attrs={'data-test-id': 'author-link'})
                    author = author.text.strip() if author else "N/A"
                    
                    date = soup.find('span', attrs={'data-test-id': 'published-on'})
                    if not date:
                        date = soup.find('time')
                    date = date.text.strip() if date else article_info.get('date', 'N/A')
                    
                    article_body = soup.find('div', attrs={'data-test-id': 'content-container'})
                    
                    if not article_body:
                        article_body = soup.find('article')
                    
                    if not article_body:
                        article_body = soup.find('div', class_=lambda c: c and 'article-content' in c)
                    
                    content = ""
                    if article_body:
                        paragraphs = article_body.find_all(['p', 'h2', 'h3', 'blockquote', 'ul', 'ol'])
                        
                        for p in paragraphs:
                            if p.find('aside') or p.find(class_=lambda c: c and ('ad' in c.lower() or 'promo' in c.lower())):
                                continue
                            
                            if p.name in ['ul', 'ol']:
                                list_items = p.find_all('li')
                                for item in list_items:
                                    content += f"• {item.text.strip()}\n"
                            else:
                                if p.name in ['h2', 'h3']:
                                    content += f"\n## {p.text.strip()}\n\n"
                                else:
                                    content += f"{p.text.strip()}\n\n"
                    
                    interactive_elements = soup.find_all('div', id=lambda x: x and 'hs-interactives' in x)
                    if interactive_elements:
                        content += "\n[인터랙티브 콘텐츠가 포함되어 있습니다 - 웹사이트에서 확인하세요]\n"
                    
                    tables = article_body.find_all('table') if article_body else []
                    table_data = []
                    
                    for table in tables:
                        rows = table.find_all('tr')
                        t_data = []
                        
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            row_data = [cell.text.strip() for cell in cells]
                            if row_data:
                                t_data.append(row_data)
                        
                        if t_data:
                            table_data.append(t_data)
                    
                    charts = soup.find_all(['img', 'figure', 'div'], class_=lambda c: c and ('chart' in str(c).lower() or 'image' in str(c).lower()))
                    chart_info = []
                    
                    for chart in charts:
                        caption = chart.find('figcaption')
                        caption_text = caption.text.strip() if caption else "차트/이미지"
                        chart_info.append(caption_text)
                    
                    article_contents[title] = {
                        'title': actual_title,
                        'author': author,
                        'date': date,
                        'content': content,
                        'url': link,
                        'method_used': method_used,
                        'tables': table_data,
                        'charts': chart_info
                    }
                    
                except Exception as e:
                    print(f"파싱 오류: {e}")
                    article_contents[title] = {
                        'error': f'Error during parsing: {str(e)}',
                        'url': link,
                        'html_snippet': html[:300] + '...' if html else None
                    }
            else:
                article_contents[title] = {
                    'error': 'Failed to fetch article content',
                    'url': link
                }
        
        return article_contents
    
    def run(self, query, ticker, search_type):
        
        results = self.get_stock_data(ticker, method="all")
        parsed_data = self.parse_stock_data(results)        
        articles_to_crawl = parsed_data['seeking_alpha'][:3]
        if search_type == "url":
            return articles_to_crawl
        
        elif search_type == "report":
            contents = ""
            
            article_contents = self.crawl_seeking_alpha_articles(articles_to_crawl)            
            
            for num, (key, value) in enumerate(article_contents.items()):
                if 'content' in value.keys():
                    contents += f"article{num+1}: {value['content']} \n"
            return contents

        else: raise ValueError("search type Error")
# class AlphaUrlSearch(AlphaSearchResults):
#     """Tool specialized for Alpha report search."""

#     name: str = "alpha_urls_search"
#     description: str = (
#         "This tool is for crawling report urls"
#     )
#     search_type: str = "url"
    
# class AlphaUrlSearch(AlphaSearchResults):
#     """Tool specialized for Alpha report search."""

#     name: str = "alpha_report_search"
#     description: str = (
#         "This tool is for crawling report scripts"
#     )
#     search_type: str = "report"