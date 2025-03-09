# main.py

import os
from dotenv import load_dotenv
load_dotenv()  # .env 파일의 환경변수 로드

# 각 노드 모듈 import
from nodes.research_supervisor import research_supervisor
from nodes.retrieve_news import retrieve_news
from nodes.retrieve_docs import retrieve_docs
from nodes.get_stock_info import get_stock_info
from nodes.write_report import write_report

# common/state_graph.py 에서 GraphState 임포트
from common.state_graph import GraphState

# langgraph에서 제공하는 StateGraph, START, END, MemorySaver 임포트
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# gpt-4o-mini 활용
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model_name="gpt-4o-mini")

# 워크플로우 생성 및 노드 등록
workflow = StateGraph(GraphState)

workflow.add_node("research_supervisor", research_supervisor)
workflow.add_node("retrieve_news", retrieve_news)
workflow.add_node("retrieve_docs", retrieve_docs)
workflow.add_node("get_stock_info", get_stock_info)
workflow.add_node("write_report", write_report)

##### 엣지 정의 예시 #####
workflow.add_edge(START, "research_supervisor")
workflow.add_edge("research_supervisor", "retrieve_news")
workflow.add_edge("research_supervisor", "retrieve_docs")
workflow.add_edge("research_supervisor", "get_stock_info")
workflow.add_edge("retrieve_news", "write_report")
workflow.add_edge("retrieve_docs", "write_report")
workflow.add_edge("get_stock_info", "write_report")
workflow.add_edge("write_report", END)

# # 체크포인터 설정 및 워크플로우 실행
# memory = MemorySaver()

app = workflow.compile()

# 초기 상태 설정
initial_state: GraphState = {
    "messages": [],
    "question": "",
    "stocks": [],
    "documents": [],
    "news": [],
    "stock_info": [],
    "answer": "",
    "rejected": "none",
    "model": model,
}

result = app.invoke(initial_state)
print(result["answer"])