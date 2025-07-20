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
)
from src.graph.nodes.base import Node
from src.models.do import RawResponse


class StockInfoNode(Node):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(model=self.DEFAULT_LLM_MODEL)
        self.executor = self.create_agent_graph()

    # FastAPI 호출 시 실행될 메서드
    def invoke(self, query: str) -> RawResponse:
        state = {"message": [HumanMessage(content=query)]}
        result = self._run(state)
        return RawResponse(answer=result.update["messages"][0].content)

    def _run(self, state: dict) -> dict:
        result = self.executor.invoke(state)
        self.logger.info(f"[StockInfoNode result]\n{result['messages'][-1].content}")
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
        # 추상 클래스 요구사항 대응용. 사용하지 않음.
        return RawResponse(answer="이 기능은 현재 사용되지 않습니다.")

    def extract_symbol_and_year(self, state: dict) -> dict:
        user_input = state["message"][0].content

        # 연도 추출
        match = re.search(r"(20\d{2})년", user_input)
        target_year = match.group(1) if match else None

        # LLM을 통해 symbol 추출
        prompt = f"""
다음 문장에서 어떤 기업의 재무정보를 요청하는지 판단하고 해당 기업의 미국 주식 티커(symbol)를 알려주세요.
오직 JSON 형식으로 응답하세요. 예시: {{"symbol": "AAPL"}}

입력: "{user_input}"
출력:
        """
        response = self.llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip().replace("```json", "").replace("```", "")

        try:
            parsed = json.loads(content)
            symbol = parsed.get("symbol", "AAPL")
        except json.JSONDecodeError:
            symbol = "AAPL"

        return {
            "symbol": symbol,
            "target_year": target_year,
            "message": state["message"],
        }

    def generate_report(self, state: dict) -> dict:
        symbol = state.get("symbol", "AAPL")
        target_year = state.get("target_year", "최근 연도")
        user_input = state["message"][0].content

        # 사용자 입력에 포함된 항목 판단
        included_sections = []
        if "손익계산서" in user_input:
            included_sections.append("손익계산서")
        if "대차대조표" in user_input:
            included_sections.append("대차대조표")
        if "현금흐름표" in user_input:
            included_sections.append("현금흐름표")
        if "재무보고서" in user_input:
            included_sections.append("재무보고서")

        # 아무것도 없으면 전체 출력
        if not included_sections:
            included_sections = ["손익계산서", "대차대조표", "현금흐름표", "재무보고서"]

        # 필요한 항목만 수집
        try:
            data = {}
            if "손익계산서" in included_sections:
                data["손익계산서"] = get_income_statement(symbol)
            if "대차대조표" in included_sections:
                data["대차대조표"] = get_balance_sheet(symbol)
            if "현금흐름표" in included_sections:
                data["현금흐름표"] = get_cash_flow_statement(symbol)
            if "재무보고서" in included_sections:
                data["재무보고서"] = get_financials(symbol)
        except Exception as e:
            return {
                "messages": [HumanMessage(content=f"❗ 재무 데이터를 불러오는 중 오류 발생: {e}")]
            }

        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        sections_str = ", ".join(included_sections)

        # LLM에게 요약 요청
        prompt = f"""
당신은 금융 애널리스트입니다. 아래는 미국 기업 {symbol}의 재무제표 중 '{sections_str}'에 해당하는 데이터입니다.

- 반드시 **{target_year}년**에 해당하는 정보만 바탕으로 분석하세요.
- 아래에 포함된 항목만 상세히 요약하세요: {sections_str}
- 다음 항목을 포함해 요약 보고서를 작성하세요:
    1. 핵심 재무 요약 (매출, 이익 등)
    2. 주목할 점 (성장성, 위험요인 등)
    3. 전체적인 평가

<재무 데이터>
{json_data}
        """

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return {"messages": [HumanMessage(content=response.content)]}

    def create_agent_graph(self):
        graph = StateGraph(state_schema=dict, input=dict, output=dict)

        graph.add_node("extract_symbol_and_year", self.extract_symbol_and_year)
        graph.add_node("generate_report", self.generate_report)

        graph.add_edge(START, "extract_symbol_and_year")
        graph.add_edge("extract_symbol_and_year", "generate_report")

        return graph.compile()
