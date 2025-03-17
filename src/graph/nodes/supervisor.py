from typing import TypedDict

from langgraph.graph import END
from langgraph.types import Command

from src.graph.nodes.base import Node


class SupervisorNode(Node):
    def __init__(self):
        super().__init__()
        self.members = []
        self.system_prompt_template = (
            "You are a supervisor tasked with managing a conversation between the"
            " following workers: {members}. Given the following user request,"
            " respond with the worker to act next. Each worker will perform a"
            " task and respond with their results and status. When finished,"
            " respond with FINISH."
        )

    @property
    def system_prompt(self):
        return self.system_prompt_template.format(members=", ".join(self.members))

    def _run(self, state: dict) -> dict:
        llm = state["llm"]
        self.members = state["members"]

        self.logger.info(f"prompt: {self.system_prompt}")

        messages = [
            {"role": "system", "content": self.system_prompt},
        ] + state["messages"]

        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END

        return Command(
            goto=goto,
            update={
                "next": goto,
            },
        )

    def _invoke(self, query: str): ...


class Router(TypedDict):
    next: list[str]
