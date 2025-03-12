import logging
import time
from .api_client import KoreaInvestmentAPI
from .stock_data_processor import StockDataProcessor
from .utils import extract_stock_codes

def get_stock_info(state):
    """
    투자정보 API 노드:
    - 한국투자증권 API를 사용하여 투자 정보를 수집하고 분석합니다.
    
    Args:
        state: 그래프 상태 객체
        
    Returns:
        dict: 업데이트된 그래프 상태
    """
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info("주식 정보 수집 시작")

    # 상태에서 종목 코드 정보 가져오기
    stock_codes = extract_stock_codes(state)
    logger.info(f"분석할 종목 코드: {stock_codes}")

    # API 클라이언트 및 데이터 처리기 초기화
    api_client = KoreaInvestmentAPI()
    data_processor = StockDataProcessor()

    # 결과 저장용 컨테이너
    stock_info_results = []

    # 각 종목에 대한 정보 수집
    for stock_code in stock_codes:
        logger.info(f"종목 코드 {stock_code} 정보 수집 중...")

        try:
            # 1. 현재 주가 정보 조회
            price_data = api_client.get_stock_price(stock_code)
            processed_price = data_processor.process_current_price(price_data)

            # API 호출 제한을 고려한 지연 추가
            time.sleep(0.5)

            # 2. 일별 주가 데이터 조회 (1년)
            daily_data = api_client.get_stock_daily_prices(stock_code)
            price_df = data_processor.process_daily_prices(daily_data)

            # 3. 기술적 지표 계산
            technical_indicators = {}
            if not price_df.empty:
                technical_indicators = data_processor.calculate_technical_indicators(price_df)

            time.sleep(0.5)

            # 4. 재무 정보 요약 조회
            financial_data = api_client.get_financial_summary(stock_code)
            processed_financial = data_processor.process_financial_data(financial_data)

            # 5. 종합 정보 구성
            stock_summary = {
                "stock_code": stock_code,
                "stock_name": processed_price.get("stock_name", ""),
                "current_price": processed_price.get("current_price", 0),
                "price_change": processed_price.get("price_change", 0),
                "price_change_percentage": processed_price.get("price_change_percentage", 0),
                "52w_high": technical_indicators.get("high_52w", 0),
                "52w_low": technical_indicators.get("low_52w", 0),
                "trading_volume": processed_price.get("volume", 0),
                "market_cap": processed_price.get("market_cap", 0),
                "per": processed_price.get("per", 0),
                "eps": processed_price.get("eps", 0),
                "pbr": processed_price.get("pbr", 0),
                "technical_indicators": technical_indicators,
                "financial_info": processed_financial
            }

            # 결과에 추가
            stock_info_results.append(stock_summary)
            logger.info(f"종목 코드 {stock_code} 정보 수집 완료")

        except Exception as e:
            logger.error(f"종목 코드 {stock_code} 정보 수집 중 오류 발생: {e}")
            # 기본 정보라도 추가 (오류가 있을 경우)
            stock_info_results.append({
                "stock_code": stock_code,
                "error": str(e)
            })

        # API 호출 제한을 고려한 지연 추가
        time.sleep(1)

    # 결과를 문자열 형태로 변환 (리포트 작성을 위한 포맷팅)
    formatted_results = []
    for stock in stock_info_results:
        if "error" in stock:
            formatted_results.append(f"{stock.get('stock_code')} 정보 조회 실패: {stock.get('error')}")
            continue

        formatted_info = (
            f"{stock.get('stock_name')} ({stock.get('stock_code')}) 현재 주가: {stock.get('current_price'):,}원, "
            f"전일대비: {stock.get('price_change'):+,}원 ({stock.get('price_change_percentage'):+.2f}%), "
            f"52주 최고가: {stock.get('52w_high'):,}원, 52주 최저가: {stock.get('52w_low'):,}원, "
            f"시가총액: {stock.get('market_cap'):,}원, PER: {stock.get('per', 0):.2f}, "
            f"PBR: {stock.get('pbr', 0):.2f}"
        )
        formatted_results.append(formatted_info)

    logger.info("주식 정보 수집 완료")

    # 상태 업데이트
    updated_state = state.copy()
    updated_state["stock_info"] = formatted_results  # 문자열 형태의 요약 정보
    updated_state["stock_data"] = stock_info_results  # 원본 데이터 (다른 노드에서 활용 가능)
    updated_state["stocks"] = stock_codes  # 분석된 종목 코드들

    return updated_state