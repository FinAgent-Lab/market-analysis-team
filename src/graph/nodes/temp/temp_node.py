import json
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START

from src.graph.nodes.usa_financial_api import *
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from src.graph.nodes.base import Node
from src.models.do import RawResponse


class TempNode(Node):
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
                        name="google_search",
                    )
                ]
            },
            goto="supervisor",
        )

    # TODO: _run 함수와 유사하게 작성. 이 함수를 이용하면, 직접 받는 API를 노출시키고 테스트할 수 있음. 실제 수퍼바이저 노드 연동과는 무관
    # 현재 google search node 기준이므로 수정이 필요해요.
    def _invoke(self, query: str) -> RawResponse:
        agent = self.agent or create_react_agent(
            ChatOpenAI(model=self.DEFAULT_LLM_MODEL),
            self.tools,
            prompt=self.system_prompt,
        )
        result = agent.invoke({"messages": [("human", query)]})
        return RawResponse(answer=result["messages"][-1].content)


    # ✅ classify 노드 정의
    def classify_message(self, state):
        user_input = state["message"][0].content
        prompt = f"""
사용자의 질문을 보고 호출할 Financial Modeling Prep API 함수를 판단해 JSON 형식으로 출력하세요.

반드시 아래 규칙을 따르세요:

1. "손익계산서" → {{"function": "get_income_statement", "symbol": "AAPL"}}
2. "대차대조표" → {{"function": "get_balance_sheet", "symbol": "AAPL"}}
3. "현금흐름표" → {{"function": "get_cash_flow_statement", "symbol": "AAPL"}}
4. "재무보고서" → {{"function": "get_financial_reports", "symbol": "AAPL"}}
5. "주요 지표" → {{"function": "get_key_metrics", "symbol": "AAPL"}}
6. "재무 비율" → {{"function": "get_ratios", "symbol": "AAPL"}}
7. "TTM 주요 지표" → {{"function": "get_key_metrics_ttm", "symbol": "AAPL"}}
8. "TTM 재무 비율" → {{"function": "get_ratios_ttm", "symbol": "AAPL"}}
9. "재무 점수" → {{"function": "get_financial_scores", "symbol": "AAPL"}}
10. "소유자 수입" → {{"function": "get_owner_earnings", "symbol": "AAPL"}}
11. "기업 가치" → {{"function": "get_enterprise_values", "symbol": "AAPL"}}
12. "손익계산서 성장" → {{"function": "get_income_statement_growth", "symbol": "AAPL"}}
13. "대차대조표 성장" → {{"function": "get_balance_sheet_growth", "symbol": "AAPL"}}
14. "현금흐름표 성장" → {{"function": "get_cash_flow_growth", "symbol": "AAPL"}}
15. "재무제표 성장" → {{"function": "get_financial_growth", "symbol": "AAPL"}}
16. "보고된 손익계산서" → {{"function": "get_income_statement_as_reported", "symbol": "AAPL"}}
17. "보고된 대차대조표" → {{"function": "get_balance_sheet_as_reported", "symbol": "AAPL"}}
18. "보고된 현금흐름표" → {{"function": "get_cash_flow_as_reported", "symbol": "AAPL"}}
19. "보고된 전체 재무제표" → {{"function": "get_financial_statement_full_as_reported", "symbol": "AAPL"}}
20. "대차대조표 분석" 또는 "유동비율", "부채비율", "자기자본비율" 등 지표 분석이 포함된 질문 → {{"function": "balance_sheet_analysis", "symbol": "AAPL"}}
21. "수익성 지표", "비용 비율", "주당 지표" 등 지표 분석이 포함된 질문 → {{"function": "income_statement_analysis", "symbol": "AAPL"}}
22. "현금 분석" 재무재표 질문 → {{"function": "cash_flow_analysis", "symbol": "AAPL"}}
23. "성장률 및 R&D 투자비율 분석" 질문 → {{"function": "growth_and_ratios_analysis", "symbol": "AAPL"}}

다른 키워드나 알 수 없는 질문은 다음을 출력:
{{"function": "fallback_node"}}

⚠️ 오직 JSON 형식만 출력하세요.
입력: {user_input}
"""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip().replace("```json", "").replace("```", "")

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            return {"function": "fallback_node"}
        return result

    # ✅ fallback 노드 정의
    def fallback_node(self, state):
        return {"message": "죄송합니다. 요청을 이해하지 못했습니다. 예: '손익계산서', '재무 비율' 등의 키워드를 사용해 주세요."}

    # ✅ 그래프 생성 함수
    def create_agent_graph(self):
        graph = StateGraph(state_schema=dict, input=dict, output=dict)

        # 노드 등록
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
        graph.add_node("fallback_node", fallback_node)

        # 엣지 연결
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
                "fallback_node": "fallback_node"
            }
        )

        executor = graph.compile()
        return executor
