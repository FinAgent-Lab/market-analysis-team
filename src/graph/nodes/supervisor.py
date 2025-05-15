from typing import TypedDict

from langgraph.graph import END
from langgraph.types import Command

from src.graph.nodes.base import Node


class SupervisorNode(Node):
    def __init__(self):
        super().__init__()
        self.members = []
        self.system_prompt_template = (
            "You are a supervisor managing a team of worker nodes: {members}. \n"
            "Your task is to coordinate these workers to fulfill the user's request, based on the full conversation history and any prior worker outputs. "
            "The team consists of the following specialized groups and their members:\n\n"
            "<News Data Collection>\n"
            "**Members:** googlesearcher, navernewssearcher, chosunrssfeeder, wsjmarketrssfeeder, weeklyreporter\n"
            "Handles all tasks related to gathering, summarizing, and extracting structured news data relevant to the subject. "
            "These workers identify key news events, sentiment, and extract useful information for the report.\n"
            "<News Data Collection/>\n\n"
            "<Financial Statement Data Collection>\n"
            "**Members:** hantoofinancialanalyzer, usfinancialanalyzer, stockinfo\n"
            "Responsible for acquiring, parsing, and verifying financial statement data (e.g., income statements, balance sheets, cash flow statements) for the subject. "
            "These workers validate data completeness and highlight missing or inconsistent information.\n"
            "<Financial Statement Data Collection/>\n\n"
            "<ESG Data Collection>\n"
            "**Members:** retrieveesg\n"
            "Gathers Environmental, Social, and Governance (ESG) scores, reports, and material events for the subject. "
            "They analyze ESG trends, identify recent issues, and ensure only credible sources are referenced.\n"
            "<ESG Data Collection/>\n\n"
            "<Report Composition>\n"
            "**Members:** reportassistant\n"
            "The report assistant node, which structures and formats all collected information into the final report. "
            "It enforces the predefined template, checks data sufficiency, and produces a report per subject.\n"
            "<Report Composition/>\n\n"
            "Instructions:\n"
            "Your task is to coordinate these workers to fulfill the user's request, based on the full conversation history and any prior worker outputs. "
            "Carefully analyze the user's request for whether it involves multiple distinct subjects (e.g., financial instruments or categories). "
            "If multiple subjects are detected, ensure that each subject is processed independently and results are returned as separate reports per subject. "
            "Each worker — except the 'reportassistantnode' — will complete a discrete subtask and report back with their results and status. "
            "You must ensure that once all necessary information is gathered, the final response strictly adheres to the predefined report format as enforced by the report assistant node — without additional commentary or structure. "
            "If a subject's report cannot be produced due to insufficient data (less than 50% of critical content), respond for that subject only with a statement indicating that a reliable report cannot be generated. "
            "Your role is to continually evaluate which worker should act next, in order to move toward complete, report-formatted answers for each requested subject."
            "When the full task is completed, respond with FINISH."
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
