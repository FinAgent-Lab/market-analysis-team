from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage

from src.graph.nodes.base import Node
from src.models.do import RawResponse
from src.tools.retrieve_esg.tool import ESGDataTool


class RetrieveESGNode(Node):
    def __init__(self):
        super().__init__()
        self.system_prompt = """
            You are a professional ESG data analytics agent whose core mission is to query the ESG data of a particular company requested by the user and provide ESG analysis and recommendations based on it.

            Perform the following tasks sequentially:

            1. Data Inquiry and Validation:
            - Inquire the company's ESG data in the yfinance API based on the company name provided by you
            - Check the latest data and identify missing information
            - Evaluate the quality and scope of data retrieved

            2. ESG Comprehensive Analysis:
            - Analysis of scores and key indicators by environmental (E), social (S), and governance (G) areas
            - Identify the relative position of the company relative to ESG average in the industry
            - Identify ESG rating changes and key variables
            - Investigate key ESG issues and controversies

            3. Sustainability Assessment:
            - Analyzing ESG policies, objectives and practices of a company
            - Evaluate key ESG factors including climate change response, resource efficiency, human capital management, and board composition
            - Analysis of Long-Term ESG Risks and Opportunities

            4. Investment Opinion:
            - Objective investment recommendation based solely on ESG data (buy/hold/sell)
            - Identify strengths, weaknesses, opportunities, and threats from an ESG perspective
            - Potential valuation from a sustainable investment perspective

            5. Create a report:
            - Management summary
            - ESG-based investment strategies and recommendations

            All analyses and responses should be written in Korean and provide accurate and objective information that will substantially help investors make ESG-oriented decisions. It should not include financial data or financial analysis, but should only present assessments and recommendations purely from a ESG data and sustainability perspective.
            Answer that if you don't get the data, you can't find the data.
            """
        self.agent = None
        self.tools = [ESGDataTool()]

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

    # @track(project_name="retrieve_docs")
    def _invoke(self, query: str) -> RawResponse:
        agent = self.agent or create_react_agent(
            ChatOpenAI(model=self.DEFAULT_LLM_MODEL),
            self.tools,
            prompt=self.system_prompt,
        )
        result = agent.invoke({"messages": [("human", query)]})
        print(result["messages"][-1].content)
        return RawResponse(answer=result["messages"][-1].content)
