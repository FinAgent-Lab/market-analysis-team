from abc import ABC, abstractmethod
from typing import Any
from typing_extensions import Self

from langgraph.graph import StateGraph, START
from src.graph.nodes.base import Node
from src.graph.nodes import (
    SupervisorNode,
)
from src.models.graph_state import SimpleState, SupervisorState
from src.utils.logger import setup_logger

logger = setup_logger("market_agent")


class BuilderABC(ABC):
    def __init__(self):
        self.logger = setup_logger("market_agent")

    @abstractmethod
    def build(self) -> Self: ...

    @abstractmethod
    def execute(self, state: SimpleState) -> Any: ...

    @abstractmethod
    def run(self): ...


class SupervisorGraphBuilder(BuilderABC):
    def __init__(self):
        super().__init__()
        self._builder = None
        self._graph = None
        self._node_list = []
        # TODO: OPENAI 라이브러리 처리

    def build(self) -> Self:
        self.logger.info("Building graph...")
        self._builder = StateGraph(SupervisorState)

        self._builder.add_node("supervisor", SupervisorNode())
        for node in self._node_list:
            self._builder.add_node(node.__class__.__name__.lower(), node)
            # self._builder.add_node(
            #     node.__class__.__name__,
            #     _make_call_agent(
            #         node,
            #         output_mode="full_history",
            #         add_handoff_back_messages=True,
            #         supervisor_name="supervisor",
            #     ),
            # )
        self.members = list(
            map(lambda x: x.__class__.__name__.lower(), self._node_list)
        )

        self._builder.add_edge(START, "supervisor")

        self._graph = self._builder.compile()

        self.logger.info("Graph built successfully")
        return self

    def execute(self, state: SupervisorState) -> Any:
        state["members"] = self.members

        self.logger.info(f"Executing graph with state: {state}")
        assert self._graph is not None, "Graph is not built"
        result = self._graph.invoke(state)
        self.logger.info(f"Execution completed with result: {result}")
        return result

    def run(self): ...

    def add_node(self, node: Node):
        self._node_list.append(node)

    def remove_node(self, node: Node):
        self._node_list.remove(node)

    def get_nodes(self) -> list[Node]:
        return self._node_list

    def get_members(self) -> list[str]:
        return self.members
