# common/state_graph.py

from typing import Annotated, TypedDict, Literal
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

# GraphState 타입 정의
# 각 에이전트 노드 개발 후 필요한 부분 추가 및 수정 예정 
class GraphState(TypedDict):
    messages: Annotated[list, add_messages]  # 메시지(누적되는 list)
    question: Annotated[str, "User's Question"]  # 질문
    stocks: Annotated[list, "Stocks"]  # 주식 종목
    documents: Annotated[list, "Retrieved Documents"]  # 문서의 검색 결과
    news: Annotated[list, "Retrieved News"] # 뉴스 검색 결과
    stock_info: Annotated[list, "Stock Information"]  # 종목 정보
    answer: Annotated[str, "LLM generated answer"]  # 답변
    model: ChatOpenAI # 각 노드에서 필요에 따라 다른 모델을 사용할 수 있도록 함
    # rejected: Annotated[Literal['news', 'documents', 'stock_info', 'none', 'all'], "rejected data"]  # 분기를 위한 state 사용?