# nodes/research_supervisor/research_supervisor.py

from common.state_graph import GraphState

def research_supervisor(state: GraphState) -> GraphState:
    """
    시장분석 에이전트팀 총괄 노드:
    TODO:
    - 질문 분석
    - 질문에 관련된 종목 추출
    - 각 에이전트 호출 지시
    """
    # 개발을 위해 임시로 삼성전자 종목 설정
    question = "삼성전자 주가 전망에 대해 알려주세요."
    stocks = ["삼성전자"]
    return {"question": question, "stocks": stocks}

### 향후 분기 routing 등등, 질문에 따라 필요한 노드만 호출 등등 구현 필요

# def retrieval_checker(state: GraphState):
#     """
#     retrieval_checker 함수는 research_supervisor 내부에서 관리하여,
#     상태(state)에 따라 다음 노드를 결정 ?
#     """
#     if state.get("rejected") == "news":
#         return "retrieve_news"
#     elif state.get("rejected") == "documents":
#         return "retrieve_docs"
#     elif state.get("rejected") == "stock_info":
#         return "get_stock_info"
#     elif state.get("rejected") == "all":
#         return ["retrieve_news", "retrieve_docs", "get_stock_info"]
#     else:
#         return "write_report"

# rework_nodes = ["retrieve_news", "retrieve_docs", "get_stock_info", "write_report"] 