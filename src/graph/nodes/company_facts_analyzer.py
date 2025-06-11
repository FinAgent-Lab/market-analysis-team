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
            "You are a tool executor. Extract the ticker from the query and use CompanyFactsTool. "
            "Your ONLY job is to return the exact output from CompanyFactsTool without any changes. "
            "DO NOT analyze, summarize, or modify the tool's output in any way. "
            "DO NOT add your own commentary or interpretation. "
            "The tool already provides perfectly formatted information. "
            "Return the tool's raw output as your final answer."
        )
        self.agent = None
        self.tools = [CompanyFactsTool()]

    def _run(self, state: dict) -> dict:
        if self.agent is None:
            assert state["llm"] is not None, "The State model should include llm"
            llm = state["llm"]
            self.agent = create_react_agent(
                llm,
                self.tools,
                prompt=self.system_prompt,
            )
        result = self.agent.invoke(state)
        self.logger.info(f"   result: \n{result['messages'][-1].content}")
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=result["messages"][-1].content,
                        name="company_facts_analyzer",
                    )
                ]
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