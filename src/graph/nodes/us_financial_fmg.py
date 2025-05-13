import json
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START

from src.graph.nodes.usa_financial_api import *
from langgraph.types import Command
from src.graph.nodes.base import Node
from src.models.do import RawResponse


class StockInfoNode(Node):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(model=self.DEFAULT_LLM_MODEL)
        self.executor = self.create_agent_graph()

    def _run(self, state: dict) -> dict:
        result = self.executor.invoke(state)
        self.logger.info(f"   result: \n{result['messages'][-1].content}")
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=result["messages"][-1].content,
                        name="market_agent",
                    )
                ]
            },
            goto="supervisor",
        )

    import json

    def _invoke(self, query: str) -> RawResponse:
        result = self.executor.invoke({"message": [HumanMessage(content=query)]})
        
        # 전체 리스트를 JSON 문자열로 변환해서 응답
        if result and isinstance(result, list):
            answer = json.dumps(result, indent=2, ensure_ascii=False)
            return RawResponse(answer=answer)
        else:
            raise ValueError(f"Unexpected result format: {result}")



    def classify_message(self, state):
        user_input = state["message"][0].content
        prompt = f"""
사용자의 질문을 보고 호출할 Financial Modeling Prep API 함수를 판단해 JSON 형식으로 출력하세요.
예: "손익계산서" → {{"function": "get_income_statement", "symbol": "AAPL"}}
입력: {user_input}
"""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip().replace("```json", "").replace("```", "")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"function": "fallback_node"}

    def fallback_node(self, state):
        return {
            "message": "죄송합니다. 요청을 이해하지 못했습니다. 예: '손익계산서', '재무 비율' 등의 키워드를 사용해 주세요."
        }

    def create_agent_graph(self):
        graph = StateGraph(state_schema=dict, input=dict, output=dict)

        graph.add_node("classify", self.classify_message)
        graph.add_node("get_income_statement", lambda s: get_income_statement(s["symbol"]))
        graph.add_node("get_balance_sheet", lambda s: get_balance_sheet(s["symbol"]))
        graph.add_node("get_cash_flow_statement", lambda s: get_cash_flow_statement(s["symbol"]))
        graph.add_node("get_financial_reports", lambda s: get_financial_reports(s["symbol"]))
        graph.add_node("get_key_metrics", lambda s: get_key_metrics(s["symbol"]))
        graph.add_node("get_ratios", lambda s: get_ratios(s["symbol"]))
        graph.add_node("get_key_metrics_ttm", lambda s: get_key_metrics_ttm(s["symbol"]))
        graph.add_node("get_ratios_ttm", lambda s: get_ratios_ttm(s["symbol"]))
        graph.add_node("get_financial_scores", lambda s: get_financial_scores(s["symbol"]))
        graph.add_node("get_owner_earnings", lambda s: get_owner_earnings(s["symbol"]))
        graph.add_node("get_enterprise_values", lambda s: get_enterprise_values(s["symbol"]))
        graph.add_node("get_income_statement_growth", lambda s: get_income_statement_growth(s["symbol"]))
        graph.add_node("get_balance_sheet_growth", lambda s: get_balance_sheet_growth(s["symbol"]))
        graph.add_node("get_cash_flow_growth", lambda s: get_cash_flow_growth(s["symbol"]))
        graph.add_node("get_financial_growth", lambda s: get_financial_growth(s["symbol"]))
        graph.add_node("get_income_statement_as_reported", lambda s: get_income_statement_as_reported(s["symbol"]))
        graph.add_node("get_balance_sheet_as_reported", lambda s: get_balance_sheet_as_reported(s["symbol"]))
        graph.add_node("get_cash_flow_as_reported", lambda s: get_cash_flow_as_reported(s["symbol"]))
        graph.add_node("get_financial_statement_full_as_reported", lambda s: get_financial_statement_full_as_reported(s["symbol"]))
        graph.add_node("balance_sheet_analysis", lambda s: balance_sheet_analysis(s["symbol"]))
        graph.add_node("income_statement_analysis", lambda s: income_statement_analysis(s["symbol"]))
        graph.add_node("cash_flow_analysis", lambda s: cash_flow_analysis(s["symbol"]))
        graph.add_node("growth_and_ratios_analysis", lambda s: growth_and_ratios_analysis(s["symbol"]))
        graph.add_node("fallback_node", self.fallback_node)

        graph.add_edge(START, "classify")
        graph.add_conditional_edges(
            source="classify",
            path=lambda x: x["function"],
            path_map={
                "get_income_statement": "get_income_statement",
                "get_balance_sheet": "get_balance_sheet",
                "get_cash_flow_statement": "get_cash_flow_statement",
                "get_financial_reports": "get_financial_reports",
                "get_key_metrics": "get_key_metrics",
                "get_ratios": "get_ratios",
                "get_key_metrics_ttm": "get_key_metrics_ttm",
                "get_ratios_ttm": "get_ratios_ttm",
                "get_financial_scores": "get_financial_scores",
                "get_owner_earnings": "get_owner_earnings",
                "get_enterprise_values": "get_enterprise_values",
                "get_income_statement_growth": "get_income_statement_growth",
                "get_balance_sheet_growth": "get_balance_sheet_growth",
                "get_cash_flow_growth": "get_cash_flow_growth",
                "get_financial_growth": "get_financial_growth",
                "get_income_statement_as_reported": "get_income_statement_as_reported",
                "get_balance_sheet_as_reported": "get_balance_sheet_as_reported",
                "get_cash_flow_as_reported": "get_cash_flow_as_reported",
                "get_financial_statement_full_as_reported": "get_financial_statement_full_as_reported",
                "balance_sheet_analysis": "balance_sheet_analysis",
                "income_statement_analysis": "income_statement_analysis",
                "cash_flow_analysis": "cash_flow_analysis",
                "growth_and_ratios_analysis": "growth_and_ratios_analysis",
                "fallback_node": "fallback_node",
            },
        )

        return graph.compile()
