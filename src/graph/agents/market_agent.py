import json
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START
from src.graph.nodes.usa_financial_api import *
import os
api_key = os.getenv("OPENAI_API_KEY")  # 환경변수로 설정


# ✅ GPT 모델 세팅 (환경변수는 FastAPI나 다른 곳에서 load_dotenv()로 설정)
gpt4o_mini = ChatOpenAI(
    openai_api_key=api_key,
    model_name="gpt-4o-mini",
    temperature=0.7,
    max_tokens=150,
)

# ✅ classify 노드 정의
def classify_message(state):
    user_input = state["message"][0].content
    prompt = f"""
사용자의 질문을 보고 호출할 Financial Modeling Prep API 함수를 판단해 JSON 형식으로 출력하세요.

다른 키워드나 알 수 없는 질문은 다음을 출력:
{{"function": "fallback_node"}}

⚠️ 오직 JSON 형식만 출력하세요.
입력: {user_input}
"""

    try:
        response = gpt4o_mini.invoke([HumanMessage(content=prompt)])
        content = response.content.strip().replace("```json", "").replace("```", "")
        print(f"[GPT 응답 원문] {content}")  # ✅ 실제 GPT 응답 확인

        result = json.loads(content)

        # ✅ 타입 확인
        if not isinstance(result, dict):
            print("[경고] GPT 응답이 dict 아님. fallback_node로 이동")
            return {"function": "fallback_node"}

        # ✅ 잘못된 함수명을 안전하게 매핑
        raw_func = result.get("function", "")
        func_map = {
            "quote": "get_stock_summary",
            "get_quote": "get_stock_summary",
            "stock_info": "get_stock_summary",
            "get_profile": "get_stock_summary",
            "get_company_profile": "get_stock_summary",
            "get_stock_quote": "get_stock_summary",
        }
        final_func = func_map.get(raw_func, raw_func)

        # ✅ 안전한 함수 목록
        valid_funcs = {
            "get_income_statement",
            "get_balance_sheet",
            "get_cash_flow_statement",
            "get_financial_reports",
            "get_key_metrics",
            "get_ratios",
            "get_key_metrics_ttm",
            "get_ratios_ttm",
            "get_financial_scores",
            "get_owner_earnings",
            "get_enterprise_values",
            "get_income_statement_growth",
            "get_balance_sheet_growth",
            "get_cash_flow_growth",
            "get_financial_growth",
            "get_income_statement_as_reported",
            "get_balance_sheet_as_reported",
            "get_cash_flow_as_reported",
            "get_financial_statement_full_as_reported",
            "balance_sheet_analysis",
            "income_statement_analysis",
            "cash_flow_analysis",
            "growth_and_ratios_analysis",
            "get_stock_summary",
        }

        if final_func not in valid_funcs:
            print(f"[경고] 잘못된 함수명 '{final_func}' → fallback_node")
            return {"function": "fallback_node"}

        print(f"[INFO] classify 결과: function={final_func}")
        return {"function": final_func}

    except Exception as e:
        print(f"[ERROR] classify_message 내부 예외: {e}")
        return {"function": "fallback_node"}




# ✅ fallback 노드 정의
def fallback_node(state):
    return {"message": "죄송합니다. 요청을 이해하지 못했습니다. 예: '손익계산서', '재무 비율' 등의 키워드를 사용해 주세요."}

# ✅ 그래프 생성 함수
def create_agent_graph():
    graph = StateGraph(state_schema=dict, input=dict, output=dict)

    # 노드 등록
    graph.add_node("classify", classify_message)
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
    graph.add_node("get_stock_summary", lambda s: get_stock_summary(s["symbol"]))
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
            "get_stock_summary": "get_stock_summary",
            "fallback_node": "fallback_node"
        }
    )

    executor = graph.compile()
    return executor