# nodes/get_stock_info/get_stock_info.py

from common.state_graph import GraphState

def get_stock_info(state: GraphState) -> GraphState:
    """
    투자정보 API 노드:
    - 한투 API 등을 사용하여 투자 정보를 가져옵니다.
    """
    stock_info = ["삼성전자 현재 주가: 55000원, 52주 최고가: 62000원, 52주 최저가: 50000원"]
    return {"stock_info": stock_info}
