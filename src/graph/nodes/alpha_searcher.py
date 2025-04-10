from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage

from src.graph.nodes.base import Node
from src.models.do import RawResponse
from src.tools.alpha_searcher.tool import AlphaUrlSearch, AlphaReportSearch


class AlphaSearcherNode(Node):
    def __init__(self):
        super().__init__()
        self.system_prompt = (
            "You are a search agent for U.S. stock market using alpha search api."
            "Summarize these url contents"
            "Do Generate additional words"
        )
        self.agent = None
        self.tools = [AlphaUrlSearch(ticker = "", search_type='url')]
        # AlphaReportSearch(ticker = "", search_type='report'),
        
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
                        name=self.__class__.__name__.lower().replace("node", ""),
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
