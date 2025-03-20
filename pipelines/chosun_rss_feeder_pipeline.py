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
        self.name = "Market Analysis - Chosun RSS Feeder"
        self.agent_name = "chosunrssfeeder"
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

        headers = {}
        headers["accept"] = "application/json"
        headers["Content-Type"] = "application/json"

        try:
            r = requests.post(
                url=f"{self.endpoint}?query={user_message}",
                json={},
                headers=headers,
            )

            r.raise_for_status()
            return ResponseBody(**r.json()).answer
        except Exception as e:
            return f"Error: {e}"
