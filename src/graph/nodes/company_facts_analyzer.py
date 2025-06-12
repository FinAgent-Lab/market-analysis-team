from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage

from src.graph.nodes.base import Node
from src.models.do import RawResponse
from src.tools.company_facts.tool import CompanyFactsTool

class CompanyFactsAnalyzerNode(Node):
    def __init__(self):
        super().__init__()

        self.system_prompt = (
            "You are a tool executor specialized in retrieving company information. "
            "Extract the ticker symbol from the user query and use the CompanyFactsTool to get detailed company information. "
            "Your ONLY job is to return the exact output from CompanyFactsTool without any changes. "
            "DO NOT analyze, summarize, or modify the tool's output in any way. "
            "DO NOT add your own commentary or interpretation. "
            "The tool already provides perfectly formatted information with proper error handling. "
            "If the tool returns an error message, pass it through exactly as provided. "
            "Return the tool's raw output as your final answer."
        )
        self.agent = None
        self.tools = [CompanyFactsTool()]

    def _run(self, state: dict) -> dict:
        try:
            if self.agent is None:
                assert state["llm"] is not None, "The State model should include llm"
                llm = state["llm"]
                self.agent = create_react_agent(
                    llm,
                    self.tools,
                    prompt=self.system_prompt,
                )
            
            result = self.agent.invoke(state)
            response_content = result['messages'][-1].content
            
            self.logger.info(f"CompanyFactsAnalyzer result: \n{response_content}")
            
            # API 키 오류 감지 및 추가 정보 제공
            if "API Key 설정 오류" in response_content or "API 초기화 실패" in response_content:
                self.logger.error("Company Facts API key configuration error detected")
                enhanced_error = response_content + """

🔧 **배포 환경 확인사항:**
• GitHub Secrets에 FINANCIAL_DATASETS_API_KEY가 설정되어 있는지 확인
• Secrets 이름이 정확한지 확인 (대소문자 구분)
• API 키가 유효하고 만료되지 않았는지 확인
• 배포 환경에서 환경 변수가 올바르게 로드되는지 확인

관리자에게 GitHub Secrets 설정을 요청하세요.
"""
                response_content = enhanced_error
            
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=response_content,
                            name="company_facts_analyzer",
                        )
                    ]
                },
                goto="supervisor",
            )
            
        except Exception as e:
            error_message = f"""
❌ **CompanyFactsAnalyzer 실행 오류**

노드 실행 중 예상치 못한 오류가 발생했습니다.

**오류 내용:** {str(e)}

**가능한 원인:**
• API 키 설정 문제
• 네트워크 연결 문제  
• LLM 모델 초기화 실패
• 도구 실행 오류

관리자에게 문의하여 시스템 상태를 확인해주세요.
"""
            self.logger.error(f"CompanyFactsAnalyzer execution error: {e}")
            
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=error_message,
                            name="company_facts_analyzer",
                        )
                    ]
                },
                goto="supervisor",
            )

    def _invoke(self, query: str) -> RawResponse:
        try:
            agent = self.agent or create_react_agent(
                ChatOpenAI(model=self.DEFAULT_LLM_MODEL),
                self.tools,
                prompt=self.system_prompt,
            )
            result = agent.invoke({"messages": [("human", query)]})
            return RawResponse(answer=result["messages"][-1].content)
            
        except Exception as e:
            error_response = f"""
❌ **회사 정보 조회 실패**

쿼리 실행 중 오류가 발생했습니다: {str(e)}

**해결 방법:**
• 올바른 티커 심볼을 입력했는지 확인 (예: AAPL, MSFT, GOOGL)
• API 키 설정이 올바른지 확인
• 네트워크 연결 상태 확인

다시 시도하거나 관리자에게 문의하세요.
"""
            self.logger.error(f"CompanyFactsAnalyzer _invoke error: {e}")
            return RawResponse(answer=error_response)