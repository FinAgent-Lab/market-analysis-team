import pandas as pd
import numpy as np
from datetime import datetime

class StockDataProcessor:
    """주식 데이터 처리 및 분석 클래스"""

    def __init__(self):
        """데이터 처리기 초기화"""
        pass

    def process_current_price(self, price_data):
        """
        현재 주가 데이터 처리

        Args:
            price_data (dict): API로부터 받은 원시 주가 데이터

        Returns:
            dict: 가공된 주가 정보
        """
        if not price_data:
            return {}

        try:
            result = {
                'stock_name': price_data.get('hts_kor_isnm', ''),
                'current_price': int(price_data.get('stck_prpr', 0)),
                'previous_price': int(price_data.get('stck_sdpr', 0)),
                'open_price': int(price_data.get('stck_oprc', 0)),
                'high_price': int(price_data.get('stck_hgpr', 0)),
                'low_price': int(price_data.get('stck_lwpr', 0)),
                'volume': int(price_data.get('acml_vol', 0)),
                'market_cap': price_data.get('hts_avls', '0').replace(',', ''),
                'per': float(price_data.get('per', 0) or 0),
                'eps': float(price_data.get('eps', 0) or 0),
                'pbr': float(price_data.get('pbr', 0) or 0),
                'dividend_yield': float(price_data.get('dvd_yld', 0) or 0),
                'price_change': int(price_data.get('prdy_vrss', 0) or 0),
                'price_change_percentage': float(price_data.get('prdy_ctrt', 0) or 0),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            return result

        except (ValueError, TypeError) as e:
            print(f"데이터 처리 중 오류 발생: {e}")
            return {}

    def process_daily_prices(self, daily_data):
        """
        일별 주가 데이터를 처리하여 DataFrame으로 변환

        Args:
            daily_data (list): API로부터 받은 원시 일별 주가 데이터

        Returns:
            pandas.DataFrame: 처리된 일별 주가 데이터
        """
        if not daily_data:
            return pd.DataFrame()

        try:
            df = pd.DataFrame(daily_data)

            # 컬럼명 변경
            df = df.rename(columns={
                'stck_bsop_date': 'date',
                'stck_clpr': 'close',
                'stck_oprc': 'open',
                'stck_hgpr': 'high',
                'stck_lwpr': 'low',
                'acml_vol': 'volume',
                'acml_tr_pbmn': 'trading_value',
                'prdy_vrss': 'price_change',
                'prdy_vrss_sign': 'change_sign'
            })

            # 필요한 컬럼만 선택
            selected_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'price_change']
            df = df[selected_columns]

            # 데이터 타입 변환
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'price_change']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])

            # 날짜 형식 변환 및 정렬
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df = df.sort_values(by='date')

            return df

        except Exception as e:
            print(f"일별 주가 데이터 처리 중 오류 발생: {e}")
            return pd.DataFrame()

    def process_financial_data(self, financial_data):
        """
        재무 데이터 처리

        Args:
            financial_data (dict): API로부터 받은 원시 재무 데이터

        Returns:
            dict: 가공된 재무 정보
        """
        if not financial_data:
            return {}

        try:
            result = {
                'revenue': financial_data.get('sales', 0),
                'operating_profit': financial_data.get('op_profit', 0),
                'net_profit': financial_data.get('net_income', 0),
                'roe': financial_data.get('roe', 0),
                'debt_ratio': financial_data.get('debt_ratio', 0),
                'quick_ratio': financial_data.get('quick_ratio', 0),
                'reserve_ratio': financial_data.get('reserve_ratio', 0),
                'eps': financial_data.get('eps', 0),
                'per': financial_data.get('per', 0),
                'bps': financial_data.get('bps', 0),
                'pbr': financial_data.get('pbr', 0),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            return result

        except Exception as e:
            print(f"재무 데이터 처리 중 오류 발생: {e}")
            return {}

    def calculate_technical_indicators(self, price_df):
        """
        기술적 지표 계산

        Args:
            price_df (pandas.DataFrame): 일별 주가 데이터프레임

        Returns:
            dict: 기술적 지표 정보
        """
        if price_df.empty:
            return {}

        try:
            # 이동평균선 계산
            price_df['MA5'] = price_df['close'].rolling(window=5).mean()
            price_df['MA20'] = price_df['close'].rolling(window=20).mean()
            price_df['MA60'] = price_df['close'].rolling(window=60).mean()
            price_df['MA120'] = price_df['close'].rolling(window=120).mean()

            # RSI 계산 (14일)
            delta = price_df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            price_df['RSI'] = 100 - (100 / (1 + rs))

            # MACD 계산
            price_df['EMA12'] = price_df['close'].ewm(span=12, adjust=False).mean()
            price_df['EMA26'] = price_df['close'].ewm(span=26, adjust=False).mean()
            price_df['MACD'] = price_df['EMA12'] - price_df['EMA26']
            price_df['MACD_Signal'] = price_df['MACD'].ewm(span=9, adjust=False).mean()

            # 볼린저 밴드 (20일)
            price_df['BB_Middle'] = price_df['close'].rolling(window=20).mean()
            price_df['BB_Std'] = price_df['close'].rolling(window=20).std()
            price_df['BB_Upper'] = price_df['BB_Middle'] + (price_df['BB_Std'] * 2)
            price_df['BB_Lower'] = price_df['BB_Middle'] - (price_df['BB_Std'] * 2)

            # 최신 데이터 추출
            latest = price_df.iloc[-1].to_dict()

            # 52주 최고가 및 최저가
            weeks_52 = price_df.iloc[-252:] if len(price_df) >= 252 else price_df
            high_52w = weeks_52['high'].max()
            low_52w = weeks_52['low'].min()

            result = {
                'ma5': latest.get('MA5'),
                'ma20': latest.get('MA20'),
                'ma60': latest.get('MA60'),
                'ma120': latest.get('MA120'),
                'rsi': latest.get('RSI'),
                'macd': latest.get('MACD'),
                'macd_signal': latest.get('MACD_Signal'),
                'bb_upper': latest.get('BB_Upper'),
                'bb_middle': latest.get('BB_Middle'),
                'bb_lower': latest.get('BB_Lower'),
                'high_52w': high_52w,
                'low_52w': low_52w,
                'current_to_high_52w_ratio': latest.get('close') / high_52w if high_52w else None,
                'current_to_low_52w_ratio': latest.get('close') / low_52w if low_52w else None
            }

            return result

        except Exception as e:
            print(f"기술적 지표 계산 중 오류 발생: {e}")
            return {}