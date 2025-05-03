from typing import TypedDict

from langgraph.graph import END
from langgraph.types import Command

from src.graph.nodes.base import Node


class SupervisorNode(Node):
    def __init__(self):
        super().__init__()
        self.members = []
        self.system_prompt_template = (
            "You are a supervisor managing a team of worker nodes: {members}. "
            "Your task is to coordinate these workers to fulfill the user's request, based on the full conversation history and any prior worker outputs. "
            "Carefully analyze the user's request for whether it involves multiple distinct subjects (e.g., financial instruments or categories). "
            "If multiple subjects are detected, ensure that each subject is processed independently and results are returned as separate reports per subject. "
            "Each worker will complete a discrete subtask and report back with their results and status. "
            "You must ensure that once all necessary information is gathered, the final response strictly adheres to the predefined report format as enforced by the report assistant node — without additional commentary or structure. "
            "If a subject's report cannot be produced due to insufficient data (less than 80% of critical content), respond for that subject only with a statement indicating that a reliable report cannot be generated. "
            "Your role is to continually evaluate which worker should act next, in order to move toward complete, report-formatted answers for each requested subject."
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
