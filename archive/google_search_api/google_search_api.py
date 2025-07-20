from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage

from src.graph.nodes.base import Node
from src.models.do import RawResponse
from src.tools.google_search_api.tool import GoogleSearchAPI


class GoogleSearchAPINode(Node):
    def __init__(self):
        super().__init__()

        # v1
        # self.system_prompt = (
        #     "You are a stock investment research assistant using the GoogleSearch API. "
        #     "Extract the stock ticker symbol from the user’s query. "
        #     'Combine the extracted ticker with relevant keywords such as "market sentiment", "news", '
        #     '"analyst opinions", and "valuation" to form a comprehensive search query in English only. '
        #     "Use the GoogleSearch tool to execute that query and retrieve results. "
        #     "Consider each result’s pubDate and prioritize the most recent relevant information. "
        #     "Base your summary strictly on the retrieved search results. "
        #     "In your detailed Korean summary, explicitly cite each item’s pubDate along with the article title, source, and key findings. "
        #     "Return only the summary. "
        #     "Do nothing else."
        # )

        # v2
        self.system_prompt = (
            "You are a stock investment research assistant using the GoogleSearch API. "
            "Extract the stock ticker symbol from the user’s query. "
            "Combine the extracted ticker with relevant keywords such as 'market sentiment', 'news', "
            "'analyst opinions', and 'valuation' to form a comprehensive search query in **English** only. "
            "Use the GoogleSearch tool to execute that query and retrieve results. "
            "For each result, attempt to extract at least one concrete key finding (e.g., data point, analyst quote, valuation metric). "
            "If a result yields no unique or substantive content, exclude it from your summaries. "
            "Consider each result’s pubDate and prioritize the most recent relevant information. "
            "Your primary goal is to provide the most comprehensive overview possible by utilizing the maximum number of relevant search results. "
            "Summarize key findings from as many distinct and valuable search results as you can—do not arbitrarily limit the number of results you summarize. "
            "Explicitly cite each item’s pubDate along with the article title, source, and key finding for all summarized items. "
            "Return more than 10 detailed **Korean** summaries strictly based on the retrieved search results, excluding any result that lacks substantive content. "
            "Do nothing else."
        )
        self.agent = None
        self.tools = [GoogleSearchAPI()]

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
                        name="google_search",
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
        # config = self._get_callback_config()
        # result = agent.invoke({"messages": [("human", query)]}, config=config)
        result = agent.invoke({"messages": [("human", query)]})
        return RawResponse(answer=result["messages"][-1].content)
