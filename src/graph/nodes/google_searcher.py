from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage

from src.graph.nodes.base import Node
from src.models.do import RawResponse
from src.tools.google_searcher.tool import GoogleSearcher


class GoogleSearcherNode(Node):
    def __init__(self):
        super().__init__()
        self.agent = None
        self.tools = [GoogleSearcher()]

    def _get_current_date_info(self) -> dict:
        """현재 날짜 정보를 동적으로 생성"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        return {
            'today_str': today.strftime("%m/%d/%Y"),
            'yesterday_str': yesterday.strftime("%m/%d/%Y"),
            'seven_days_ago': (today - timedelta(days=7)).strftime("%m/%d/%Y"),
            'thirty_days_ago': (today - timedelta(days=30)).strftime("%m/%d/%Y"),
            'current_year': today.year,
            'current_month': today.month
        }

    def _get_system_prompt(self) -> str:
        """동적으로 시스템 프롬프트 생성"""
        date_info = self._get_current_date_info()
        
        return f"""You are a news research specialist using Google News searcher specialized in US stock market research.
Your job is to extract search queries and date ranges from user requests, then use the GoogleSearcher tool to find relevant news articles about US stocks and companies.

**CURRENT DATE INFORMATION:**
- Today's date: {date_info['today_str']}
- Yesterday's date: {date_info['yesterday_str']}
- Current year: {date_info['current_year']}
- Current month: {date_info['current_month']}

**SEARCH QUERY OPTIMIZATION FOR US STOCKS:**
1. Convert Korean company names to English stock symbols or company names:
   - '애플' → 'Apple' or 'AAPL'
   - '테슬라' → 'Tesla' or 'TSLA'
   - '마이크로소프트' → 'Microsoft' or 'MSFT'
   - '구글' → 'Google' or 'Alphabet' or 'GOOGL'
   - '아마존' → 'Amazon' or 'AMZN'
   - '메타' → 'Meta' or 'META'
   - '엔비디아' → 'NVIDIA' or 'NVDA'
   - '넷플릭스' → 'Netflix' or 'NFLX'
   - '삼성전자' → 'Samsung Electronics' (for ADR: Samsung)

2. Use English keywords for better US news search results:
   - Add relevant keywords: 'stock', 'earnings', 'price', 'market', 'shares'
   - For financial news: 'revenue', 'profit', 'quarterly results', 'analyst'
   - For market movements: 'stock price', 'trading', 'NYSE', 'NASDAQ'

3. Optimize search terms for US financial media:
   - Prefer official company names and stock symbols
   - Include sector-specific terms when relevant
   - Use standard financial terminology

**DATE EXTRACTION RULES:**
1. Analyze the user query for time expressions:
   - '최근 일주일', '지난 일주일', '한 주일', '7일' → Search last 7 days
   - '최근 한달', '지난 한달', '30일' → Search last 30 days
   - '최근 이주일', '2주일', '14일' → Search last 14 days
   - '오늘' → Search from yesterday to today (start_date = {date_info['yesterday_str']}, end_date = {date_info['today_str']})
   - '어제' → Search yesterday only (start_date and end_date both = {date_info['yesterday_str']})
   - '4월', 'April' → Search entire April of current year ({date_info['current_year']})
   - '2024년 5월' → Search May 2024
   - Specific dates like '2024-01-01부터 2024-01-31까지' → Use exact dates
   - If NO time expression is found → Default to last 30 days

2. Calculate the appropriate start_date and end_date in MM/DD/YYYY format:
   - For relative dates: calculate from today's date ({date_info['today_str']})
   - For 'today': start_date = {date_info['yesterday_str']}, end_date = {date_info['today_str']} (yesterday to today)
   - For 'yesterday': use {date_info['yesterday_str']} for both start_date and end_date
   - For 'last 7 days': start_date = {date_info['seven_days_ago']}, end_date = {date_info['today_str']}
   - For 'last 30 days': start_date = {date_info['thirty_days_ago']}, end_date = {date_info['today_str']}
   - For specific months: use first and last day of that month
   - For exact dates: convert YYYY-MM-DD to MM/DD/YYYY format

3. Extract and translate search query:
   - Remove: '최근', '지난', '일주일', '한달', '4월', '2024년', '오늘', '어제', specific dates, etc.
   - Translate Korean company names to English
   - Add relevant English financial keywords
   - Keep main focus on US stock market context

**TOOL USAGE:**
Use the GoogleSearcher tool with these parameters:
- query: the translated and optimized English search term for US stocks
- start_date: calculated start date in MM/DD/YYYY format
- end_date: calculated end date in MM/DD/YYYY format (always use {date_info['today_str']} for current date)
- max_results: 10 (default)

**EXAMPLES:**
User: '애플 최근 일주일'
→ Translated query: 'Apple stock AAPL'
→ Date range: 7 days ago to today
→ Call: GoogleSearcher(query='Apple stock AAPL', start_date='{date_info['seven_days_ago']}', end_date='{date_info['today_str']}')

User: '테슬라 오늘'
→ Translated query: 'Tesla TSLA stock'
→ Date range: Yesterday to today
→ Call: GoogleSearcher(query='Tesla TSLA stock', start_date='{date_info['yesterday_str']}', end_date='{date_info['today_str']}')

User: '구글 어제'
→ Translated query: 'Google Alphabet GOOGL stock'
→ Date range: Yesterday only
→ Call: GoogleSearcher(query='Google Alphabet GOOGL stock', start_date='{date_info['yesterday_str']}', end_date='{date_info['yesterday_str']}')

User: '테슬라 4월 실적'
→ Translated query: 'Tesla TSLA earnings revenue'
→ Date range: April 1st to April 30th of current year
→ Call: GoogleSearcher(query='Tesla TSLA earnings revenue', start_date='04/01/{date_info['current_year']}', end_date='04/30/{date_info['current_year']}')

User: '마이크로소프트 주가 뉴스'
→ Translated query: 'Microsoft MSFT stock price'
→ Date range: Default 30 days (no time expression found)
→ Call: GoogleSearcher(query='Microsoft MSFT stock price', start_date='{date_info['thirty_days_ago']}', end_date='{date_info['today_str']}')

User: '엔비디아 AI 관련 소식'
→ Translated query: 'NVIDIA NVDA AI artificial intelligence'
→ Date range: Default 30 days
→ Call: GoogleSearcher(query='NVIDIA NVDA AI artificial intelligence', start_date='{date_info['thirty_days_ago']}', end_date='{date_info['today_str']}')

**STOCK SYMBOL REFERENCE:**
- Apple: AAPL
- Tesla: TSLA  
- Microsoft: MSFT
- Google/Alphabet: GOOGL, GOOG
- Amazon: AMZN
- Meta: META
- NVIDIA: NVDA
- Netflix: NFLX
- Berkshire Hathaway: BRK.A, BRK.B
- Johnson & Johnson: JNJ
- JPMorgan Chase: JPM
- Visa: V
- Procter & Gamble: PG
- Home Depot: HD
- Mastercard: MA
- UnitedHealth: UNH
- Disney: DIS
- Coca-Cola: KO
- Intel: INTC
- Cisco: CSCO
- Verizon: VZ
- Pfizer: PFE
- Walmart: WMT
- McDonald's: MCD

**IMPORTANT REMINDERS:**
- ALWAYS translate Korean company names to English equivalents
- ALWAYS use stock symbols when available for better search results
- ALWAYS use {date_info['today_str']} as end_date for current/recent searches
- ALWAYS calculate dates relative to today ({date_info['today_str']})
- When no date is specified, default to 30 days ending today
- Remove ALL date expressions from the search query
- Focus on US stock market and financial news sources
- Use standard financial terminology in English

**OUTPUT:**
Return the exact output from GoogleSearcher without any modifications. 
DO NOT analyze, summarize, or add your own commentary. 
The tool already provides perfectly formatted news information with proper error handling."""

    def _run(self, state: dict) -> dict:
        try:
            if self.agent is None:
                assert state["llm"] is not None, "The State model should include llm"
                llm = state["llm"]
                self.agent = create_react_agent(
                    llm,
                    self.tools,
                    prompt=self._get_system_prompt(),  # 동적 프롬프트 사용
                )
            
            result = self.agent.invoke(state)
            response_content = result['messages'][-1].content
            
            # 로깅을 DEBUG 레벨로 변경 (운영시에는 출력되지 않음)
            self.logger.debug(f"GoogleSearcher result: \n{response_content}")
            
            # 검색 오류 감지 및 추가 정보 제공
            if "Searcher 초기화 실패" in response_content or "검색 중 오류" in response_content:
                self.logger.error("Google Searcher error detected")
                enhanced_error = response_content + """

🔧 **검색 환경 확인사항:**
• 네트워크 연결 상태 확인
• Google의 요청 제한(Rate Limiting) 확인
• User-Agent 설정 확인
• BeautifulSoup 파싱 로직 확인

검색이 차단되었을 수 있습니다. 잠시 후 다시 시도해주세요.
"""
                response_content = enhanced_error

            # 정상 경로에서 return 문 추가
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=response_content,
                            name="google_searcher",
                        )
                    ]
                },
                goto="supervisor",
            )
        
        except Exception as e:
            # 에러 로깅만 유지
            self.logger.error(f"GoogleSearcher execution error: {e}")
            error_message = f"""
❌ **GoogleSearcher 실행 오류**

노드 실행 중 예상치 못한 오류가 발생했습니다.

**오류 내용:** {str(e)}

**가능한 원인:**
• 네트워크 연결 문제
• Google의 검색 차단
• BeautifulSoup 파싱 오류
• LLM 모델 초기화 실패

관리자에게 문의하여 시스템 상태를 확인해주세요.
"""
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=error_message,
                            name="google_searcher",
                        )
                    ]
                },
                goto="supervisor",
            )
            
    def _invoke(self, query: str) -> RawResponse:
        try:
            # 에이전트가 없으면 새로 생성 (동적 프롬프트 사용)
            if self.agent is None:
                self.agent = create_react_agent(
                    ChatOpenAI(model=self.DEFAULT_LLM_MODEL),
                    self.tools,
                    prompt=self._get_system_prompt(),
                )
            
            result = self.agent.invoke({"messages": [("human", query)]})
            return RawResponse(answer=result["messages"][-1].content)
            
        except Exception as e:
            error_response = f"""
❌ **Google News 검색 실패**

쿼리 실행 중 오류가 발생했습니다: {str(e)}

**해결 방법:**
• 검색어를 명확하게 입력했는지 확인
• 네트워크 연결 상태 확인
• Google의 요청 제한 확인
• 잠시 후 다시 시도

다시 시도하거나 관리자에게 문의하세요.
"""
            self.logger.error(f"GoogleSearcher _invoke error: {e}")
            return RawResponse(answer=error_response)
