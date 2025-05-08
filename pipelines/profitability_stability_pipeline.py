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
        self.name = "Market Analysis - Profitability & Stability Analyzer"
        self.agent_name = "usfinancialstatementanalyzer"
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

        # Extract stock ticker or company name from user message
        query = user_message.strip()

        # Check if the query is valid
        if not query:
            return "Please provide a company name or stock ticker symbol (e.g., Apple, AAPL, Microsoft, MSFT)"

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
                return f"Error: The US Stock Profitability & Stability Analysis service is not available. Please check if the service is running."
            elif "Connection" in error_message:
                return f"Error: Could not connect to the analysis service. Please check your network connection."
            else:
                return f"Error analyzing profitability and stability metrics: {e}"