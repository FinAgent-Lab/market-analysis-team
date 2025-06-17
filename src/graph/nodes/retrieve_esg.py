from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from opik import track

from src.graph.nodes.base import Node
from src.models.do import RawResponse
from src.tools.retrieve_esg.tool import ESGDataTool


class RetrieveESGNode(Node):
    def __init__(self):
        super().__init__()
        self.system_prompt = """
            You are an agent that retrieves ESG (Environmental, Social, and Governance) data for companies requested by users.
            For questions from a long-term or continuous perspective, please also inquire ESG data.
            Your response must ONLY be a valid JSON object with no additional text, explanation, or markdown formatting.

            When given a company name or ticker symbol, return ESG data in this exact JSON format:
            {
            "ticker": "[ticker symbol]",
            "company_name": "[company name]",
            "total_esg_score": {
                "score": [numeric score],
                "risk_level": "[Negligible, Low, Medium, High, Severe]"
            },
            "environment_score": {
                "score": [numeric score],
            },
            "social_score": {
                "score": [numeric score],
            },
            "governance_score": {
                "score": [numeric score],
            },
            "rating_year": [year as integer],
            "rating_month": [month as integer],
            }

            Use the following criteria STRICTLY and EXACTLY to determine risk levels:

            For total_esg_score:
            - IF score >= 0 AND score < 10, THEN risk_level = "Negligible"
            - IF score >= 10 AND score < 20, THEN risk_level = "Low" 
            - IF score >= 20 AND score < 30, THEN risk_level = "Medium"
            - IF score >= 30 AND score < 40, THEN risk_level = "High"
            - IF score >= 40, THEN risk_level = "Severe"

            Critical rules:
            1. Return ONLY the JSON object with no other text, explanation, or commentary.
            2. Do NOT include backticks (```) or any markdown formatting around the JSON.
            3. Numeric values should be numbers without quotes (not strings).
            4. For each score, you MUST follow the exact risk level criteria specified above with no exceptions or deviations.
            5. If a value is unavailable or unknown, use the string "정보 없음" instead of null.
            6. NO ROUNDING or approximation when determining risk levels - use the exact score value and the exact boundary values in the criteria.
            7. DOUBLE-CHECK each risk level assignment to ensure it exactly matches the criteria.
            8. NEVER use your own judgment to adjust the risk levels - follow the criteria exactly as specified.


            Remember: The supervisor node will handle all explanations and formatting for the end user. Your job is ONLY to provide the raw data in the specified JSON format with STRICTLY CORRECT risk levels according to the criteria.
            """
        self.agent = None
        self.tools = [ESGDataTool()]

    @track(project_name="retrieve_docs")
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

    @track(project_name="retrieve_docs")
    def _invoke(self, query: str) -> RawResponse:
        agent = self.agent or create_react_agent(
            ChatOpenAI(model=self.DEFAULT_LLM_MODEL),
            self.tools,
            prompt=self.system_prompt,
        )
        # config = self._get_callback_config()
        # result = agent.invoke({"messages": [("human", query)]}, config=config)
        result = agent.invoke({"messages": [("human", query)]})
        print(result["messages"][-1].content)
        return RawResponse(answer=result["messages"][-1].content)
