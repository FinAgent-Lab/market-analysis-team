from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from src.graph.nodes.base import Node
from src.models.do import RawResponse
from src.tools.hantoo_stock.tool import HantooFinancialStatementTool


class HantooFinancialAnalyzerNode(Node):
    def __init__(self):
        super().__init__()
        self.system_prompt = (
            "You are a financial statement analysis agent using Korea Investment & Securities API. "
            "Your task is to analyze balance sheets, income statements, and financial ratios "
            "to provide a comprehensive assessment of a company's financial health, growth potential, and profitability. "
            "Always identify the stock code in the user's query and provide accurate, data-driven analysis. "
            "Present your findings clearly and concisely, but do not provide investment advice or recommendations. "
            "If a specific stock code isn't mentioned, ask for clarification."
        )
        self.agent = None
        self.tools = [HantooFinancialStatementTool()]

    def _run(self, state: dict) -> Command:
        if self.agent is None:
            assert state["llm"] is not None, "The State model should include llm"
            llm = state["llm"]
            self.agent = create_react_agent(
                llm,
                self.tools,
                prompt=self.system_prompt,
            )

        # Run the agent
        result = self.agent.invoke(state)

        self.logger.info(
            f"Financial analysis result: \n{result['messages'][-1].content}"
        )

        # Extract the stock code
        stock_code = self._extract_stock_code_from_result(
            result["messages"][-1].content
        )

        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=result["messages"][-1].content,
                        name="hantoo_financial_analyzer",
                    )
                ],
                # Store analysis results in structured format
                "financial_analysis": {
                    "stock_code": stock_code,
                    "analysis_text": result["messages"][-1].content,
                },
            },
            goto="supervisor",
        )

    def _invoke(self, query: str) -> RawResponse:
        agent = self.agent or create_react_agent(
            ChatOpenAI(model=self.DEFAULT_LLM_MODEL),
            self.tools,
            prompt=self.system_prompt,
        )
        result = agent.invoke({"messages": [("human", query)]})
        return RawResponse(answer=result["messages"][-1].content)

    def _extract_stock_code_from_result(self, result_text: str) -> str:
        """Extract stock code from result text"""
        import re

        # Try to find patterns like "Stock Code 005930"
        match = re.search(r"Stock Code (\d{6})", result_text)
        if match:
            return match.group(1)

        # Try alternative patterns
        match = re.search(r"stock code[:\s]*(\d{6})", result_text, re.IGNORECASE)
        if match:
            return match.group(1)

        # Try to find "company with code XXXXXX" pattern
        match = re.search(r"company with code (\d{6})", result_text, re.IGNORECASE)
        if match:
            return match.group(1)

        # More general pattern - find any 6-digit number in the text
        match = re.search(r"(\d{6})", result_text)
        if match:
            return match.group(1)

        return "unknown"
