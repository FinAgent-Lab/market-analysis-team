# nodes/write_report/write_report.py

from common.state_graph import GraphState

def write_report(state: GraphState) -> GraphState:
    """
    보고서 작성 노드:
    - 최종적으로 LLM을 사용하여 보고서를 생성합니다.
    """
    question = state["question"]
    documents = state["documents"]
    news = state["news"]
    stock_info = state["stock_info"]
    model = state["model"]

    # 시스템 프롬프트 예시
    system_prompt = """
    당신은 금융 분석 전문가입니다. 주어진 정보를 바탕으로 투자자가 이해하기 쉽게 분석 보고서를 작성해주세요.
    객관적인 데이터와 사실에 기반하여 답변하고, 중요한 투자 포인트를 명확히 요약해주세요.
    예측은 제공된 정보에 기반해야 하며, 근거 없는 주장은 피해주세요.
    """

    # 사용자 메시지 구성 예시
    user_message = f"""
    질문: {question}

    참고 문서: 
    {documents}

    관련 뉴스: 
    {news}

    종목 정보:
    {stock_info}
    """

    answer = model.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    ).content

    return {"answer": answer}