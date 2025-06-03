import json
import re
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START
from langgraph.types import Command

from src.graph.nodes.usa_financial_api import (
    get_income_statement,
    get_balance_sheet,
    get_cash_flow_statement,
    get_financials,
    get_key_metrics,
    get_financial_ratios,
    get_financial_scores,
    get_enterprise_value,
    get_income_statement_growth,
    get_balance_sheet_growth,
    get_cash_flow_statement_growth,
    get_financials_growth,
)
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
                        name="stockinfo_agent",
                    )
                ]
            },
            goto="supervisor",
        )

    def _invoke(self, query: str) -> RawResponse:
        result = self.executor.invoke({"message": [HumanMessage(content=query)]})
        if result and isinstance(result, dict) and "messages" in result:
            return RawResponse(answer=result["messages"][-1].content)
        else:
            raise ValueError(f"Unexpected result format: {result}")

    def classify_message(self, state):
        user_input = state["message"][0].content

        # 연도 추출
        match = re.search(r"(20\d{2})년(?:도)?", user_input)
        target_year = match.group(1) if match else None
        print(f"match = {target_year}")

        prompt = f"""
다음 사용자의 질문을 보고, 구체적인 재무 API 함수를 호출할지, 아니면 전반적인 분석을 위해 여러 API를 호출해야 할지를 판단해 주세요.

출력 형식은 아래 중 하나입니다:

1. 단일 API 호출:
{{"function": "get_income_statement", "symbol": "AAPL"}}
    1. "손익계산서" → {{"function": "get_income_statement", "symbol": "AAPL"}}
    2. "대차대조표" → {{"function": "get_balance_sheet", "symbol": "AAPL"}}
    3. "현금흐름표" → {{"function": "get_cash_flow_statement", "symbol": "AAPL"}}
    4. "재무보고서" → {{"function": "get_financials", "symbol": "AAPL"}}
    5. "주요 지표" → {{"function": "get_key_metrics", "symbol": "AAPL"}}
    6. "재무 비율" → {{"function": "get_financial_ratios", "symbol": "AAPL"}}
    7. "재무 점수" → {{"function": "get_financial_scores", "symbol": "AAPL"}}
    8. "기업 가치" → {{"function": "get_enterprise_value", "symbol": "AAPL"}}
    9. "손익계산서 성장" → {{"function": "get_income_statement_growth", "symbol": "AAPL"}}
    10. "대차대조표 성장" → {{"function": "get_balance_sheet_growth", "symbol": "AAPL"}}
    11. "현금흐름표 성장" → {{"function": "get_cash_flow_statement_growth", "symbol": "AAPL"}}

2. 종합 분석 요청 (여러 지표 필요):
{{"function": "comprehensive_analysis", "symbol": "AAPL"}}

입력: {user_input}
"""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip().replace("```json", "").replace("```", "")
        try:
            parsed = json.loads(content)
            if target_year:
                parsed["target_year"] = target_year
            return parsed
        except json.JSONDecodeError:
            return {"function": "fallback_node"}

    def fallback_node(self, state):
        return {
            "messages": [
                HumanMessage(content="죄송합니다. 요청을 이해하지 못했습니다. 예: '손익계산서', '재무 비율' 등의 키워드를 사용해 주세요.")
            ]
        }

    def run_comprehensive_analysis(self, state):
        symbol = state["symbol"]
        result = {
            "income": get_income_statement(symbol),
            "balance": get_balance_sheet(symbol),
            "cashflow": get_cash_flow_statement(symbol),
            "ratios": get_financial_ratios(symbol),
            "metrics": get_key_metrics(symbol),
        }
        return {"symbol": symbol, "result": result}

    def summarize_report(self, state):
        symbol = state.get("symbol", "Unknown")
        api_result = state.get("result", {})
        content = json.dumps(api_result, indent=2, ensure_ascii=False)
        target_year = state.get("target_year")
        print(f"****** target year ******** = {target_year}")
        prompt = f"""
당신은 금융 애널리스트입니다. 아래는 {symbol}의 재무 데이터입니다.

아래 지시를 반드시 따르세요:
- **오직 {target_year}년**에 해당하는 데이터만 사용하여 분석하세요.
- 다른 연도의 데이터는 절대 포함하지 마세요.

이 데이터를 기반으로 유의미한 정보를 파악하여 간결한 재무제표 분석 보고서를 작성하세요.

요약은 다음 항목을 포함하세요:
1. 핵심 재무 요약 (매출, 이익 등)
2. 주목할 점 (성장, 위험 등)
3. 전체적인 평가

주의사항. 특정 년도 입력이 들어올 경우, 특정 년도에 대한 내용으로만 보고서를 작성하세요.

<재무 데이터>
{content}
"""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {"messages": [HumanMessage(content=response.content)]}

    def create_agent_graph(self):
        graph = StateGraph(state_schema=dict, input=dict, output=dict)

        graph.add_node("classify", self.classify_message)

        graph.add_node("get_income_statement", lambda s: {"symbol": s["symbol"], "result": get_income_statement(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("get_balance_sheet", lambda s: {"symbol": s["symbol"], "result": get_balance_sheet(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("get_cash_flow_statement", lambda s: {"symbol": s["symbol"], "result": get_cash_flow_statement(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("get_financials", lambda s: {"symbol": s["symbol"], "result": get_financials(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("get_key_metrics", lambda s: {"symbol": s["symbol"], "result": get_key_metrics(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("get_financial_ratios", lambda s: {"symbol": s["symbol"], "result": get_financial_ratios(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("get_financial_scores", lambda s: {"symbol": s["symbol"], "result": get_financial_scores(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("get_enterprise_value", lambda s: {"symbol": s["symbol"], "result": get_enterprise_value(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("get_income_statement_growth", lambda s: {"symbol": s["symbol"], "result": get_income_statement_growth(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("get_balance_sheet_growth", lambda s: {"symbol": s["symbol"], "result": get_balance_sheet_growth(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("get_cash_flow_statement_growth", lambda s: {"symbol": s["symbol"], "result": get_cash_flow_statement_growth(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("get_financials_growth", lambda s: {"symbol": s["symbol"], "result": get_financials_growth(s["symbol"]), "target_year": s.get("target_year")})
        graph.add_node("comprehensive_analysis", self.run_comprehensive_analysis)
        graph.add_node("fallback_node", self.fallback_node)
        graph.add_node("summarize_report", self.summarize_report)

        graph.add_edge(START, "classify")

        graph.add_conditional_edges(
            source="classify",
            path=lambda x: x["function"],
            path_map={
                "get_income_statement": "get_income_statement",
                "get_balance_sheet": "get_balance_sheet",
                "get_cash_flow_statement": "get_cash_flow_statement",
                "get_financials": "get_financials",
                "get_financial_ratios": "get_financial_ratios",
                "get_key_metrics": "get_key_metrics",
                "get_financial_scores": "get_financial_scores",
                "get_enterprise_value": "get_enterprise_value",
                "get_income_statement_growth": "get_income_statement_growth",
                "get_balance_sheet_growth": "get_balance_sheet_growth",
                "get_cash_flow_statement_growth": "get_cash_flow_statement_growth",
                "get_financials_growth": "get_financials_growth",
                "comprehensive_analysis": "comprehensive_analysis",
                "fallback_node": "fallback_node",
            },
        )

        for api_node in [
            "get_income_statement", "get_balance_sheet", "get_cash_flow_statement",
            "get_financials", "get_key_metrics", "get_financial_ratios",
            "get_financial_scores", "get_enterprise_value",
            "get_income_statement_growth", "get_balance_sheet_growth",
            "get_cash_flow_statement_growth", "get_financials_growth",
            "comprehensive_analysis"
        ]:
            graph.add_edge(api_node, "summarize_report")

        return graph.compile()
