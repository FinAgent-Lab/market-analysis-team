# import os
# import json
# from langchain_core.messages import HumanMessage
# from langchain_openai import ChatOpenAI
# from langgraph.graph import StateGraph, START
# from src.graph.nodes.usa_financial_api import (
#     get_income_statement,
#     get_balance_sheet,
#     get_cash_flow_statement,
#     get_financials,
#     get_key_metrics,
#     get_financial_ratios,
#     get_financial_scores,
#     get_enterprise_value,
#     get_income_statement_growth,
#     get_balance_sheet_growth,
#     get_cash_flow_statement_growth,
# )

# api_key = os.getenv("OPENAI_API_KEY")  # 환경변수로 설정

# gpt4o_mini = ChatOpenAI(
#     openai_api_key=api_key,
#     model_name="gpt-4o-mini",
#     temperature=0.7,
#     max_tokens=150,
# )

# def classify_message(state):
#     user_input = state["message"][0].content
#     prompt = f"""
# 사용자의 질문을 보고 호출할 Financial Modeling Prep API 함수를 판단해 JSON 형식으로 출력하세요.

# 반드시 필수로 아래 규칙을 따르세요:

# 1. "손익계산서" → {{"function": "get_income_statement", "symbol": "AAPL"}}
# 2. "대차대조표" → {{"function": "get_balance_sheet", "symbol": "AAPL"}}
# 3. "현금흐름표" → {{"function": "get_cash_flow_statement", "symbol": "AAPL"}}
# 4. "재무보고서" → {{"function": "get_financials", "symbol": "AAPL"}}
# 5. "주요 지표" → {{"function": "get_key_metrics", "symbol": "AAPL"}}
# 6. "재무 비율" → {{"function": "get_financial_ratios", "symbol": "AAPL"}}
# 7. "재무 점수" → {{"function": "get_financial_scores", "symbol": "AAPL"}}
# 8. "기업 가치" → {{"function": "get_enterprise_value", "symbol": "AAPL"}}
# 9. "손익계산서 성장" → {{"function": "get_income_statement_growth", "symbol": "AAPL"}}
# 10. "대차대조표 성장" → {{"function": "get_balance_sheet_growth", "symbol": "AAPL"}}
# 11. "현금흐름표 성장" → {{"function": "get_cash_flow_statement_growth", "symbol": "AAPL"}}

# 다른 키워드나 알 수 없는 질문은 다음을 출력:
# {{"function": "fallback_node"}}

# ⚠️ 오직 JSON 형식만 출력하세요.
# 입력: {user_input}
# """
#     response = gpt4o_mini.invoke([HumanMessage(content=prompt)])
#     content = response.content.strip().replace("```json", "").replace("```", "")

#     try:
#         result = json.loads(content)
#     except json.JSONDecodeError:
#         return {"function": "fallback_node"}
#     return result

# def fallback_node(state):
#     return {"message": "죄송합니다. 요청을 이해하지 못했습니다. 예: '손익계산서', '재무 비율' 등의 키워드를 사용해 주세요."}

# def create_agent_graph():
#     graph = StateGraph(state_schema=dict, input=dict, output=dict)

#     # 노드 등록
#     graph.add_node("classify", classify_message)
#     graph.add_node("get_income_statement", lambda s: get_income_statement(s["symbol"]))
#     graph.add_node("get_balance_sheet", lambda s: get_balance_sheet(s["symbol"]))
#     graph.add_node("get_cash_flow_statement", lambda s: get_cash_flow_statement(s["symbol"]))
#     graph.add_node("get_financials", lambda s: get_financials(s["symbol"]))
#     graph.add_node("get_key_metrics", lambda s: get_key_metrics(s["symbol"]))
#     graph.add_node("get_financial_ratios", lambda s: get_financial_ratios(s["symbol"]))
#     graph.add_node("get_financial_scores", lambda s: get_financial_scores(s["symbol"]))
#     graph.add_node("get_enterprise_value", lambda s: get_enterprise_value(s["symbol"]))
#     graph.add_node("get_income_statement_growth", lambda s: get_income_statement_growth(s["symbol"]))
#     graph.add_node("get_balance_sheet_growth", lambda s: get_balance_sheet_growth(s["symbol"]))
#     graph.add_node("get_cash_flow_statement_growth", lambda s: get_cash_flow_statement_growth(s["symbol"]))
#     graph.add_node("fallback_node", fallback_node)

#     # 엣지 연결
#     graph.add_edge(START, "classify")
#     graph.add_conditional_edges(
#         source="classify",
#         path=lambda x: x["function"],
#         path_map={
#             "get_income_statement": "get_income_statement",
#             "get_balance_sheet": "get_balance_sheet",
#             "get_cash_flow_statement": "get_cash_flow_statement",
#             "get_financials": "get_financials",
#             "get_key_metrics": "get_key_metrics",
#             "get_financial_ratios": "get_financial_ratios",
#             "get_financial_scores": "get_financial_scores",
#             "get_enterprise_value": "get_enterprise_value",
#             "get_income_statement_growth": "get_income_statement_growth",
#             "get_balance_sheet_growth": "get_balance_sheet_growth",
#             "get_cash_flow_statement_growth": "get_cash_flow_statement_growth",
#             "fallback_node": "fallback_node"
#         }
#     )

#     executor = graph.compile()
#     return executor