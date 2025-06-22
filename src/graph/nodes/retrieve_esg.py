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
        self.system_prompt = """You are a professional ESG data analyst that provides structured ESG metrics in JSON format.

TASK: Extract ESG data using the tool and return ONLY a JSON object with exact formatting.

REQUIRED JSON FORMAT:
{
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "total_esg_score": {
        "score": 18.99,
        "industry_average": 16.85,
        "vs_industry": "worse",
        "risk_level": "Low"
    },
    "environment_score": {
        "score": 2.44,
        "industry_average": 1.11,
        "vs_industry": "worse"
    },
    "social_score": {
        "score": 7.98,
        "industry_average": 7.71,
        "vs_industry": "worse"
    },
    "governance_score": {
        "score": 8.58,
        "industry_average": 8.64,
        "vs_industry": "better"
    },
    "rating_year": 2024,
    "rating_month": 7
}

CRITICAL CALCULATION RULES:

1. RISK LEVEL (based on total_esg_score only):
   • 0-9.99: "Negligible"
   • 10-19.99: "Low"
   • 20-29.99: "Medium"
   • 30-39.99: "High"
   • 40+: "Severe"

2. VS_INDUSTRY COMPARISON (lower ESG scores = better performance):
   • If |company_score - industry_average| ≤ 0.5: "similar"
   • If company_score > industry_average + 0.5: "worse"
   • If company_score < industry_average - 0.5: "better"

MANDATORY REQUIREMENTS:
- Return ONLY JSON (no backticks, no text, no explanations)
- Use exact numeric values from tool output
- Apply calculation rules precisely
- Example: Score 18.99 → risk_level "Low" (not "Medium")
- Example: Score 18.99 vs Industry 16.85 → vs_industry "worse" (18.99 > 16.85 + 0.5)"""
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
