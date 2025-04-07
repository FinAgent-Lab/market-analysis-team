from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from src.graph.nodes.base import Node
from src.models.do import RawResponse
from src.tools.us_stock.tool import USFinancialStatementTool

class USFinancialAnalyzerNode(Node):
    def __init__(self):
        super().__init__()
        self.system_prompt = (
            "You are a financial statement analysis agent for US stocks. "
            "Your task is to analyze balance sheets, income statements, and financial ratios "
            "to provide a comprehensive assessment of a company's financial health, growth potential, and profitability. "
            "Users can mention either a company name (like Apple, Microsoft) or a ticker symbol (like AAPL, MSFT). "
            "Present your findings clearly and concisely, but do not provide investment advice or recommendations. "
            "Only if no company name or ticker can be identified, ask for clarification. "
            "Always include the analyzed ticker symbol in your response using this format: 'Ticker: XXX'."
        )
        self.agent = None
        self.tools = [USFinancialStatementTool()]

    def _run(self, state: dict) -> Command:
        if self.agent is None:
            assert state["llm"] is not None, "The State model should include llm"
            llm = state["llm"]

            # LLM 참조를 도구의 속성에 추가
            self.tools[0].llm = llm

            self.agent = create_react_agent(
                llm,
                self.tools,
                prompt=self.system_prompt,
            )

        # 사용자 메시지 추출
        user_message = state["messages"][-1].content

        # 도구에서 티커 심볼 추출 (LLM 사용)
        extracted_ticker = self.tools[0]._extract_ticker(user_message)

        self.logger.info(f"[DEBUG] Ticker extracted: {extracted_ticker}")

        # 에이전트 실행
        result = self.agent.invoke(state)

        analysis_text = result['messages'][-1].content
        self.logger.info(f"US Financial analysis result: \n{analysis_text}")

        # 추출된 티커가 있으면 그대로 사용, 없으면 unknown
        ticker = extracted_ticker if extracted_ticker else "unknown"

        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=analysis_text,
                        name="us_financial_analyzer",
                    )
                ],
                # Store analysis results in structured format
                "financial_analysis": {
                    "ticker": ticker,
                    "market": "US",
                    "analysis_text": analysis_text,
                }
            },
            goto="supervisor",
        )

    def _invoke(self, query: str) -> RawResponse:
        agent = self.agent or create_react_agent(
            ChatOpenAI(model=self.DEFAULT_LLM_MODEL),
            self.tools,
            prompt=self.system_prompt,
        )

        # _invoke 호출 시에도 LLM 설정
        if not hasattr(self.tools[0], 'llm') or self.tools[0].llm is None:
            self.tools[0].llm = ChatOpenAI(model=self.DEFAULT_LLM_MODEL)

        result = agent.invoke({"messages": [("human", query)]})
        return RawResponse(answer=result["messages"][-1].content)