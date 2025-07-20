import os
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import requests

APISERVER_HOST = os.getenv("APISERVER_HOST")


class RequestBody(BaseModel):
    query: str
    model: str
    temperature: float


class ResponseBody(BaseModel):
    answer: str


class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.name = "Market Analysis - Google News Searcher"
        self.agent_name = "googlesearcher"
        self.endpoint = f"http://{APISERVER_HOST}/api/{self.agent_name}"
        pass

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # This is where you can add your custom pipelines like RAG.
        print(f"pipe:{__name__}")

        print("messages: ", messages)
        print("user_message: ", user_message)
        print("body: ", body)

        # Extract search query from user message
        query = user_message.strip()

        # Check if the query is valid
        if not query:
            return "뉴스 검색을 위한 검색어를 입력해주세요 (예: 애플 최근 일주일, 테슬라 오늘, Microsoft 주가 뉴스)"

        # Validate that query contains meaningful content for news search
        if len(query) < 2:
            return "검색어가 너무 짧습니다. 회사명이나 주식 관련 키워드를 포함해주세요."

        headers = {}
        headers["accept"] = "application/json"
        headers["Content-Type"] = "application/json"

        try:
            r = requests.post(
                url=f"{self.endpoint}?query={query}",
                json={},
                headers=headers,
            )

            r.raise_for_status()
            return ResponseBody(**r.json()).answer
        except Exception as e:
            error_message = str(e)
            if "404" in error_message:
                return "오류: Google News 검색 서비스를 사용할 수 없습니다. 서비스가 실행 중인지 확인해주세요."
            elif "Connection" in error_message:
                return "오류: Google News 검색 서비스에 연결할 수 없습니다. 네트워크 연결을 확인해주세요."
            elif "timeout" in error_message.lower():
                return "오류: 요청 시간이 초과되었습니다. Google의 요청 제한일 수 있으니 잠시 후 다시 시도해주세요."
            else:
                return f"Google News 검색 중 오류 발생: {e}"
