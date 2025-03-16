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
    timestamp: str


class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.
        # self.id = "openai_pipeline"
        self.name = "Market Analysis - Main"
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

        # payload = {**body}
        payload = RequestBody(
            query=user_message, model="gpt-4o-mini", temperature=1.0
        ).model_dump()

        try:
            r = requests.post(
                url=f"http://{APISERVER_HOST}/api/query",
                json=payload,
                headers=headers,
                # stream=True,
            )

            r.raise_for_status()
            print("supervisor return :", ResponseBody(**r.json()).answer)

            return ResponseBody(**r.json()).answer
        except Exception as e:
            return f"Error: {e}"
