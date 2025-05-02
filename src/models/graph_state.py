from typing import TypedDict, Annotated, Any

from langgraph.graph import add_messages
from langgraph.prebuilt.chat_agent_executor import AgentState

"""
각 에이전트의 필요에 따른 State 결합은 mixin 방식을 사용하면 어떨지?
=> State 내의 필드는 겹치지 않도록 주의

class A:
    a: int

class B:
    b: str

class C(A, B):
    (a: int)
    (b: str)
    c: bool

# Example
c = C(a=1, b="2", c=True)
c.a # 1
c.b # "2"
c.c # True
"""


class SimpleState(TypedDict):
    input: str
    model_name: str
    query: str
    output: str
    messages: Annotated[list, add_messages]


# TODO: llm 모델은 DI 컨테이너를 통해서 받는게 나을지도(관리 편의성)
class SupervisorState(AgentState):
    llm: Any
    members: list[str]
