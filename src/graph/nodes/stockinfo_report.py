import os
import json
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_community.tools import ReadFileTool
from src.graph.nodes.base import Node


class ReportAgentNode(Node):
    def __init__(self):
        super().__init__()
        self.agent = None
        self.template_path = os.path.join("assets", "report_template.md")
        self.tools = [ReadFileTool()]
        self.template_content = self._load_template()

        self.system_prompt = f"""
        당신은 미국 주식의 재무 데이터를 분석하여 보고서를 작성하는 전문가입니다.
        사용자 질문과 API에서 수집한 재무 데이터를 기반으로 아래의 보고서 템플릿을 엄격히 준수하여 마크다운 형식의 분석 보고서를 작성하세요.

        ## 템플릿
{self.template_content}

        주의: 반드시 위 템플릿 형식으로만 응답하며, 자유 양식의 설명은 허용되지 않습니다.
        """

    def _load_template(self):
        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[오류] 템플릿 불러오기 실패: {e}")
            return ""

    def _run(self, state: dict) -> Command:
        if self.agent is None:
            llm = state.get("llm") or ChatOpenAI(model=self.DEFAULT_LLM_MODEL)
            self.agent = create_react_agent(llm, self.tools, prompt=self.system_prompt)

        # 사용자 쿼리와 API 응답 정보 추출
        user_message = state["message"][-1].content
        financial_data = state.get("financial_data", {})

        merged_input = f"""
        사용자 요청:
        {user_message}

        재무 데이터:
        {json.dumps(financial_data, indent=2, ensure_ascii=False)}
        """

        result = self.agent.invoke({"messages": [("human", merged_input)]})

        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=result["messages"][-1].content,
                        name="reportagent"
                    )
                ],
                "report_markdown": result["messages"][-1].content,
            },
            goto="supervisor"
        )

    def _invoke(self, query: str):
        if self.agent is None:
            self.agent = create_react_agent(
                ChatOpenAI(model=self.DEFAULT_LLM_MODEL),
                self.tools,
                prompt=self.system_prompt
            )
        result = self.agent.invoke({"messages": [("human", query)]})
        return result["messages"][-1].content
