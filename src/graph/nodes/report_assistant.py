from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_community.tools.file_management.write import WriteFileTool
from langchain_core.messages import HumanMessage

from src.graph.nodes.base import Node


class ReportAssistantNode(Node):
    def __init__(self):
        super().__init__()
        self.agent = None
        self.tools = [WriteFileTool()]

    def _run(self, state: dict) -> dict:
        if self.agent is None:
            llm = state["llm"]
            self.agent = create_react_agent(
                llm,
                self.tools,
            )
        result = self.agent.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=result["messages"][-1].content, name="report_assistant"
                    )
                ]
            },
            goto="supervisor",
        )

    def _invoke(self, query: str) -> dict:
        agent = self.agent or create_react_agent(
            ChatOpenAI(model=self.DEFAULT_LLM_MODEL),
            self.tools,
        )
        print(query)
        result = agent.invoke({"messages": [("human", query)]})
        return result["messages"][-1].content
