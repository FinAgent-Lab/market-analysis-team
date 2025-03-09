# nodes/retrieve_docs/retrieve_docs.py

from common.state_graph import GraphState

def retrieve_docs(state: GraphState) -> GraphState:
    """
    문서 검색 노드:
    - 데이터베이스나 저장된 레포트를 기반으로 문서를 검색 및 요약합니다.
    - 실시간 처리 방식 및 DB 구축 방식을 모두 고려
    - PDF파일 등 document parser 활용 고려
    """
    documents = ["분석 레포트에 따르면, 삼성전자의 주가가 저평가되어 있습니다."]
    return {"documents": documents}
