from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage

from src.graph.nodes.base import Node
from src.models.do import RawResponse
from src.tools.edgar_report.tool import EdgarReporter


class EdgarReportNode(Node):
    def __init__(self):
        super().__init__()
        self.agent = None
        self.tools = [EdgarReporter()]

    def _get_system_prompt(self) -> str:
        """SEC EDGAR 보고서 분석 시스템 프롬프트"""
        return """You are a SEC EDGAR report analysis specialist focused on US public companies.
Your job is to extract company identifiers and report types from user requests, then use the EdgarReporter tool to analyze SEC filings.

**COMPANY IDENTIFICATION:**
1. Convert Korean company names to English equivalents:
   - '애플' → 'Apple' or 'AAPL'
   - '테슬라' → 'Tesla' or 'TSLA'
   - '마이크로소프트' → 'Microsoft' or 'MSFT'
   - '구글' → 'Google' or 'Alphabet' or 'GOOGL'
   - '아마존' → 'Amazon' or 'AMZN'
   - '메타' → 'Meta' or 'META'
   - '엔비디아' → 'NVIDIA' or 'NVDA'

2. Accept multiple input formats:
   - Company names: 'Apple Inc', 'Tesla Inc', 'Microsoft Corporation'
   - Stock tickers: 'AAPL', 'TSLA', 'MSFT', 'GOOGL'
   - CIK numbers: '320193', '1318605', '789019'

**REPORT TYPE EXTRACTION:**
1. Identify report type from user query:
   - '10-K', '연간보고서', '연례보고서', 'annual report' → Use '10-K'
   - '10-Q', '분기보고서', 'quarterly report' → Use '10-Q'
   - Default to '10-K' if not specified

2. Common Korean terms:
   - '사업보고서' → '10-K'
   - '분기보고서' → '10-Q'
   - '연간 실적' → '10-K'
   - '분기 실적' → '10-Q'

**QUERY OPTIMIZATION:**
1. Extract clean company identifier:
   - Remove: '의', '에 대한', '관련', '정보', '보고서', '분석'
   - Focus on core company name or ticker
   - Translate Korean to English equivalents

2. Examples:
   - '애플의 10-K 보고서' → company_identifier='Apple', report_type='10-K'
   - '테슬라 분기보고서' → company_identifier='Tesla', report_type='10-Q'
   - 'MSFT 연간보고서 분석' → company_identifier='MSFT', report_type='10-K'
   - 'NVDA 사업보고서' → company_identifier='NVDA', report_type='10-K'

**TOOL USAGE:**
Use the EdgarReporter tool with these parameters:
- company_identifier: the translated and cleaned company name, ticker, or CIK
- report_type: '10-K' or '10-Q' (default: '10-K')

**STOCK SYMBOL REFERENCE:**
- Apple: AAPL (CIK: 320193)
- Tesla: TSLA (CIK: 1318605)
- Microsoft: MSFT (CIK: 789019)
- Google/Alphabet: GOOGL (CIK: 1652044)
- Amazon: AMZN (CIK: 1018724)
- Meta: META (CIK: 1326801)
- NVIDIA: NVDA (CIK: 1045810)
- Netflix: NFLX (CIK: 1065280)
- Berkshire Hathaway: BRK.A, BRK.B (CIK: 1067983)
- JPMorgan Chase: JPM (CIK: 19617)

**EXAMPLES:**
User: '애플 10-K 보고서 분석해줘'
→ Call: EdgarReporter(company_identifier='Apple', report_type='10-K')

User: 'TSLA 분기보고서'
→ Call: EdgarReporter(company_identifier='TSLA', report_type='10-Q')

User: '마이크로소프트 사업보고서'
→ Call: EdgarReporter(company_identifier='Microsoft', report_type='10-K')

User: '구글 연간 실적'
→ Call: EdgarReporter(company_identifier='Google', report_type='10-K')

User: '320193 보고서'  # Apple's CIK
→ Call: EdgarReporter(company_identifier='320193', report_type='10-K')

**IMPORTANT REMINDERS:**
- ALWAYS translate Korean company names to English equivalents
- ALWAYS use standard report types ('10-K' or '10-Q')
- Default to '10-K' when report type is unclear
- Handle both company names and stock tickers
- Support CIK numbers as identifiers
- Remove unnecessary Korean particles and words

**OUTPUT:**
Return the exact output from EdgarReporter without any modifications.
DO NOT analyze, summarize, or add your own commentary.
The tool already provides comprehensive SEC filing analysis with proper formatting."""

    def _run(self, state: dict) -> dict:
        try:
            if self.agent is None:
                assert state["llm"] is not None, "The State model should include llm"
                llm = state["llm"]
                self.agent = create_react_agent(
                    llm,
                    self.tools,
                    prompt=self._get_system_prompt(),
                )
            
            result = self.agent.invoke(state)
            response_content = result['messages'][-1].content
            
            # 로깅을 DEBUG 레벨로 변경
            self.logger.debug(f"EdgarReport result: \n{response_content}")
            
            # 검색 오류 감지 및 추가 정보 제공
            if "초기화 실패" in response_content or "분석 중 오류" in response_content:
                self.logger.error("Edgar Reporter error detected")
                enhanced_error = response_content + """

🔧 **EDGAR API 확인사항:**
• SEC EDGAR API 접근 권한 확인
• 네트워크 연결 상태 확인
• CIK/티커 유효성 확인
• 요청 제한(Rate Limiting) 확인

SEC 서버 문제일 수 있습니다. 잠시 후 다시 시도해주세요.
"""
                response_content = enhanced_error

            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=response_content,
                            name="edgar_report",
                        )
                    ]
                },
                goto="supervisor",
            )
        
        except Exception as e:
            self.logger.error(f"EdgarReport execution error: {e}")
            error_message = f"""
❌ **Edgar Reporter 실행 오류**

노드 실행 중 예상치 못한 오류가 발생했습니다.

**오류 내용:** {str(e)}

**가능한 원인:**
• SEC EDGAR API 접근 문제
• 네트워크 연결 문제
• 회사 식별자 오류
• LLM 모델 초기화 실패

관리자에게 문의하여 시스템 상태를 확인해주세요.
"""
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=error_message,
                            name="edgar_report",
                        )
                    ]
                },
                goto="supervisor",
            )
            
    def _invoke(self, query: str) -> RawResponse:
        try:
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
❌ **SEC EDGAR 보고서 분석 실패**

쿼리 실행 중 오류가 발생했습니다: {str(e)}

**해결 방법:**
• 회사명이나 티커를 정확하게 입력했는지 확인
• 지원되는 보고서 타입(10-K, 10-Q) 확인
• 네트워크 연결 상태 확인
• SEC EDGAR API 상태 확인

다시 시도하거나 관리자에게 문의하세요.
"""
            self.logger.error(f"EdgarReport _invoke error: {e}")
            return RawResponse(answer=error_response)