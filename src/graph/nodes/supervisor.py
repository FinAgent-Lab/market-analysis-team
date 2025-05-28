import os
from typing import TypedDict

from langgraph.graph import END
from langgraph.types import Command
from langfuse import Langfuse

from src.graph.nodes.base import Node
from src.utils.const import PROMPT_SUPERVISOR, LANGFUSE_PROMPT_MAPPER


class SupervisorNode(Node):
    def __init__(self):
        super().__init__()
        self.members = []
        self.system_prompt_template = PROMPT_SUPERVISOR

        self.langfuse_enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
        if self.langfuse_enabled:
            self.langfuse = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
        else:
            self.langfuse = None

    @property
    def system_prompt(self):
        if self.langfuse_enabled:
            langfuse_prompt = self.langfuse.get_prompt(
                name=LANGFUSE_PROMPT_MAPPER[self.__class__.__name__.lower()],
                label="production",
                cache_ttl_seconds=0,
            ).get_langchain_prompt()
        else:
            langfuse_prompt = None
        prompt = langfuse_prompt or self.system_prompt_template
        return prompt.format(members=", ".join(self.members))

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
