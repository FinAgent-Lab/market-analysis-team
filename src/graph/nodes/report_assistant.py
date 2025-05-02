import os

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage

from src.graph.nodes.base import Node


class ReportAssistantNode(Node):
    def __init__(self):
        super().__init__()
        self.agent = None
        self.template_path = os.path.join("assets", "report_template.md")
        # self.tools = [WriteFileTool()]
        self.tools = []
        self.template_content = self._load_template()

    def _run(self, state: dict) -> dict:
        if self.agent is None:
            llm = state["llm"]
            self.agent = create_react_agent(
                llm,
                self.tools,
            )

        # 템플릿 내용을 직접 지시사항에 포함
        template_instruction = f"""당신은 보고서 작성 전문가입니다. 
항상 마크다운 형식의 보고서 형태로 응답해야 합니다.
어떤 질문이나 요청이 들어와도 반드시 보고서 형식으로 정리하여 제공하세요.
보고서는 다음 템플릿을 엄격히 따라야 합니다:
        다음은 보고서 템플릿입니다:
        
        {self.template_content}
        
        위 템플릿에 맞춰 주어진 정보를 바탕으로 보고서를 작성해주세요.
        """

        # 기존 메시지에 템플릿 지시사항 추가
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            enhanced_content = f"{template_instruction}\n\n{last_message.content}"
            messages = messages[:-1] + [HumanMessage(content=enhanced_content)]
            state["messages"] = messages

        result = self.agent.invoke(state)
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

    def _invoke(self, query: str) -> dict:
        agent = self.agent or create_react_agent(
            ChatOpenAI(model=self.DEFAULT_LLM_MODEL),
            self.tools,
        )
        # 템플릿 내용을 직접 지시사항에 포함
        template_instruction = f"""
        다음은 보고서 템플릿입니다:
        
        {self.template_content}
        
        위 템플릿에 맞춰 주어진 정보를 바탕으로 보고서를 작성해주세요.
        """

        enhanced_query = f"{template_instruction}\n\n{query}"
        result = agent.invoke({"messages": [("human", enhanced_query)]})
        return result["messages"][-1].content

    def _load_template(self):
        """템플릿 파일을 직접 읽어오는 메서드"""
        try:
            with open(self.template_path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            print(f"템플릿 파일을 읽는 중 오류 발생: {e}")
            return "템플릿을 불러올 수 없습니다."
