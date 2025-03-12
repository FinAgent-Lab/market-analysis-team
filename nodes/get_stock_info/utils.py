import re

def extract_stock_codes(state):
    """
    질문과 메시지에서 관련 주식 종목코드를 추출합니다.

    Args:
        state: 그래프 상태 객체

    Returns:
        list: 추출된 종목코드 리스트
    """
    # 기본 종목코드 (테스트용 또는 명시적으로 언급되지 않은 경우)
    default_codes = ["005930"]  # 삼성전자

    # 이미 분석된 종목코드가 있는 경우
    if state.get("stocks") and len(state.get("stocks")) > 0:
        return state.get("stocks")

    # 질문에서 종목 이름 또는 코드 추출 시도
    question = state.get("question", "")
    messages = state.get("messages", [])

    # 정규식 패턴 (한국 주식 종목코드: 숫자 6자리)
    code_pattern = r'\b\d{6}\b'

    # 자주 언급되는 주요 종목들의 매핑
    stock_name_to_code = {
        "삼성전자": "005930",
        "SK하이닉스": "000660",
        "현대차": "005380",
        "현대자동차": "005380",
        "기아": "000270",
        "네이버": "035420",
        "카카오": "035720",
        "LG전자": "066570",
        "삼성바이오로직스": "207940",
        "삼성SDI": "006400",
        "POSCO홀딩스": "005490",
        "포스코홀딩스": "005490",
        "셀트리온": "068270",
        "KB금융": "105560",
        "신한지주": "055550",
        "신한금융지주": "055550",
        "하나금융지주": "086790",
        "LG화학": "051910",
        "삼성물산": "028260",
        "SK이노베이션": "096770"
    }

    found_codes = []

    # 종목코드 직접 찾기
    found_codes.extend(re.findall(code_pattern, question))

    # 종목명으로 찾기
    for name, code in stock_name_to_code.items():
        if name in question:
            found_codes.append(code)

    # 메시지 내용에서도 검색
    for message in messages:
        if isinstance(message, dict) and "content" in message:
            content = message.get("content", "")
            found_codes.extend(re.findall(code_pattern, content))
            for name, code in stock_name_to_code.items():
                if name in content:
                    found_codes.append(code)

    # 중복 제거
    found_codes = list(set(found_codes))

    # 결과가 없으면 기본값 반환
    if not found_codes:
        return default_codes

    return found_codes