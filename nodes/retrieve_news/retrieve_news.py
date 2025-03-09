# nodes/retrieve_news/retrieve_news.py

from common.state_graph import GraphState

def retrieve_news(state: GraphState) -> GraphState:
    """
    뉴스 검색 노드:
    - 네이버 뉴스 API 등을 활용해 관련 뉴스를 검색
    - tavily 등도 사용 고려
    - 관련성이 높은 기사를 선별하는 로직 필요
    """
    # 결과물 출력을 위한 샘플
    news = ["삼성전자의 기술 혁신 소식이 주요 뉴스로 떠오르고 있습니다."]
    return {"news": news}
