import requests
import pprint
import os

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 불러오기
API_KEY = os.getenv("FINANCIAL_API_KEY")

def get_income_statement(symbol='AAPL', limit=3):
    print("손익계산서 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/income-statement?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()[:limit]
    return {"error": response.text}

def get_balance_sheet(symbol='AAPL', limit=3):
    print("📊 대차대조표 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        print("API 호출 실패:", response.text)
        return {"error": response.text}

    try:
        data = response.json()[:limit]
        print(f"\n{'Fiscal Year':<12} | {'Total Assets':>15} | {'Liabilities':>15} | {'Equity':>15}")
        print("-" * 65)
        for item in data:
            fy = item.get("fiscalYear", "N/A")
            assets = item.get("totalAssets", 0)
            liabilities = item.get("totalLiabilities", 0)
            equity = item.get("totalEquity", 0)

            print(f"{fy:<12} | {assets:>15,} | {liabilities:>15,} | {equity:>15,}")
        
        return data  # 필요하면 정제된 원본도 반환
    except Exception as e:
        print("처리 중 오류:", str(e))
        return {"error": str(e)}


def get_cash_flow_statement(symbol='AAPL'):
    print("현금흐름표 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/cash-flow-statement?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_financial_reports(symbol='AAPL'):
    print("재무 보고서 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/financial-reports-dates?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_key_metrics(symbol='AAPL'):
    print("주요지표 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/key-metrics?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_ratios(symbol='AAPL'):
    print("재무 비율 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/ratios?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_key_metrics_ttm(symbol='AAPL'):
    print("주요 지표 TTM Agent 호출")
    url = f"https://financialmodelingprep.com/stable/key-metrics-ttm?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_ratios_ttm(symbol='AAPL'):
    print("TTM 비율 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/ratios-ttm?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_financial_scores(symbol='AAPL'):
    print("재무 점수 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/financial-scores?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_owner_earnings(symbol='AAPL'):
    print("소유자 수입 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/owner-earnings?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_enterprise_values(symbol='AAPL'):
    print("기업 가치 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/enterprise-values?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_income_statement_growth(symbol='AAPL'):
    print("손익 계산서 성장 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/income-statement-growth?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_balance_sheet_growth(symbol='AAPL'):
    print("대차대조표 명세서 성장 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/balance-sheet-statement-growth?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_cash_flow_growth(symbol='AAPL'):
    print("현금 흐름 보고서 성장 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/cash-flow-statement-growth?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_financial_growth(symbol='AAPL'):
    print("재무재표 성장 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/financial-growth?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_income_statement_as_reported(symbol='AAPL'):
    print("보고된 손익 계산서 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/income-statement-as-reported?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_balance_sheet_as_reported(symbol='AAPL'):
    print("보고된 잔액 명세서 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/balance-sheet-statement-as-reported?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_cash_flow_as_reported(symbol='AAPL'):
    print("보고된 현금 흐름 보고서 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/cash-flow-statement-as-reported?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_financial_statement_full_as_reported(symbol='AAPL'):
    print("보고된 재무재표 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/financial-statement-full-as-reported?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def balance_sheet_analysis(symbol='AAPL', limit=3):
    print("유동성 지표, 레버리지 지표 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:

        balance_data = response.json()[:limit]
    ratios = {}

    # 유동성
    try:
        ratios['Current Ratio'] = round(
            balance_data['totalCurrentAssets'] / balance_data['totalCurrentLiabilities'], 2)
    except:
        ratios['Current Ratio'] = None

    try:
        ratios['Quick Ratio'] = round(
            (balance_data['cashAndCashEquivalents'] +
             balance_data['netReceivables'] +
             balance_data['shortTermInvestments']) / balance_data['totalCurrentLiabilities'], 2)
    except:
        ratios['Quick Ratio'] = None

    # 레버리지
    try:
        ratios['Debt to Equity'] = round(balance_data['totalLiabilities'] / balance_data['totalEquity'], 2)
    except:
        ratios['Debt to Equity'] = None

    try:
        ratios['Equity Ratio'] = round(balance_data['totalEquity'] / balance_data['totalAssets'], 2)
    except:
        ratios['Equity Ratio'] = None

    try:
        ratios['Net Debt to Equity'] = round(balance_data['netDebt'] / balance_data['totalEquity'], 2)
    except:
        ratios['Net Debt to Equity'] = None

    return {"balance_sheet_ratios": ratios}

def income_statement_analysis(symbol='AAPL', limit=3):
    print("수익성 지표, 비용 비율, 주당 지표 Agent 호출")

    url = f"https://financialmodelingprep.com/stable/income-statement?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": response.text}

    data_list = response.json()
    if not data_list:
        return {"error": "API로부터 데이터를 받지 못했습니다."}

    data = data_list[0]  # 단일 연도 분석
    revenue = data.get("revenue", 0)

    try:
        revenue = float(revenue)
    except:
        return {"error": "revenue 값이 유효하지 않습니다."}

    if revenue == 0:
        return {"error": "revenue가 0입니다. 분석 불가."}

    result = {}

    # 수익성 지표
    try: result["gross_profit_margin"] = round(data.get("grossProfit", 0) / revenue * 100, 2)
    except: pass
    try: result["operating_margin"] = round(data.get("operatingIncome", 0) / revenue * 100, 2)
    except: pass
    try: result["net_profit_margin"] = round(data.get("netIncome", 0) / revenue * 100, 2)
    except: pass
    try: result["ebitda_margin"] = round(data.get("ebitda", 0) / revenue * 100, 2)
    except: pass
    try: result["pretax_margin"] = round(data.get("incomeBeforeTax", 0) / revenue * 100, 2)
    except: pass

    # 비용 비율
    try: result["rd_intensity"] = round(data.get("researchAndDevelopmentExpenses", 0) / revenue * 100, 2)
    except: pass
    try: result["sga_ratio"] = round(data.get("sellingGeneralAndAdministrativeExpenses", 0) / revenue * 100, 2)
    except: pass
    try: result["tax_rate"] = round(data.get("incomeTaxExpense", 0) / data.get("incomeBeforeTax", 1) * 100, 2)
    except: pass
    try: result["depreciation_ratio"] = round(data.get("depreciationAndAmortization", 0) / revenue * 100, 2)
    except: pass

    # 주당 지표
    try: result["eps"] = round(data.get("netIncome", 0) / data.get("weightedAverageShsOut", 1), 2)
    except: pass
    try: result["eps_diluted"] = round(data.get("netIncome", 0) / data.get("weightedAverageShsOutDil", 1), 2)
    except: pass
    try: result["revenue_per_share"] = round(data.get("revenue", 0) / data.get("weightedAverageShsOut", 1), 2)
    except: pass

    return {"income_statement_analysis_result": result}

def cash_flow_analysis(symbol='AAPL'):
    print("현금 분석 Agent 호출")

    # API 요청
    url = f"https://financialmodelingprep.com/stable/cash-flow-statement?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": response.text}

    data_list = response.json()
    if not data_list:
        return {"error": "API로부터 데이터를 받지 못했습니다."}

    data = data_list[0]  # 가장 최근 연도 데이터 사용
    result = {}

    # 필요한 항목 추출
    operating_cf = data.get("operatingCashFlow", 0)
    capital_expend = data.get("capitalExpenditure", 0)
    net_income = data.get("netIncome", 0)
    investing_cf = data.get("investingCashFlow", 0)
    financing_cf = data.get("financingCashFlow", 0)
    revenue = data.get("revenue", 0)

    try:
        # 잉여현금흐름 (Free Cash Flow)
        result["free_cash_flow"] = round(operating_cf - capital_expend, 2)
    except:
        pass

    try:
        # 영업현금흐름 마진
        result["operating_cash_flow_margin"] = round(operating_cf / revenue * 100, 2)
    except:
        pass

    try:
        # 순이익 대비 현금 창출 비율
        result["cash_conversion_ratio"] = round(operating_cf / net_income, 2)
    except:
        pass

    try:
        # 총현금흐름
        total_cash_flow = operating_cf + investing_cf + financing_cf

        # 영업활동 비중
        result["operating_cf_ratio"] = round(operating_cf / total_cash_flow * 100, 2)

        # 투자활동 비중
        result["investing_cf_ratio"] = round(investing_cf / total_cash_flow * 100, 2)

        # 재무활동 비중
        result["financing_cf_ratio"] = round(financing_cf / total_cash_flow * 100, 2)
    except:
        pass

    try:
        # 영업현금흐름 대비 자본적지출 비율
        result["capex_to_operating_cf"] = round(capital_expend / operating_cf, 2)
    except:
        pass

    try:
        # 순이익 대비 자본적지출 비율
        result["capex_to_net_income"] = round(capital_expend / net_income, 2)
    except:
        pass

    return {"cash_flow_analysis_result": result}

def growth_and_ratios_analysis(symbol='AAPL', limit=2):
    print("성장률 및 R&D 투자비율 분석 Agent 호출")

    url = f"https://financialmodelingprep.com/stable/income-statement?symbol={symbol}&limit={limit}&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": response.text}

    data_list = response.json()
    if len(data_list) < 2:
        return {"error": "성장률 계산을 위해 최소 2개 연도의 데이터가 필요합니다."}

    current = data_list[0]  # 최신 연도
    previous = data_list[1]  # 이전 연도

    result = {}

    # 매출 성장률
    try:
        result["revenue_growth_rate"] = round(
            (current["revenue"] - previous["revenue"]) / previous["revenue"] * 100, 2
        )
    except:
        result["revenue_growth_rate"] = None

    # EPS 및 EPS 성장률
    try:
        current_eps = current["netIncome"] / current["weightedAverageShsOut"]
        previous_eps = previous["netIncome"] / previous["weightedAverageShsOut"]
        result["eps"] = round(current_eps, 2)
        result["eps_growth_rate"] = round((current_eps - previous_eps) / previous_eps * 100, 2)
    except:
        result["eps_growth_rate"] = None

    # R&D 투자비율 (현재 연도 기준)
    try:
        result["rd_intensity"] = round(current["researchAndDevelopmentExpenses"] / current["revenue"] * 100, 2)
    except:
        result["rd_intensity"] = None

    return {"growth_and_ratios_analysis_result": result}

def get_stock_summary(symbol):
    from src.graph.api_client import fetch_from_fmp
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={YOUR_API_KEY}"
    data = fetch_from_fmp(url)
    if not data:
        return {"message": f"{symbol}에 대한 요약 정보를 불러올 수 없습니다."}
    
    info = data[0]
    return {
        "symbol": info.get("symbol"),
        "name": info.get("name"),
        "price": info.get("price"),
        "marketCap": info.get("marketCap"),
        "peRatio": info.get("pe"),
        "changesPercentage": info.get("changesPercentage"),
        "dayHigh": info.get("dayHigh"),
        "dayLow": info.get("dayLow"),
        "yearHigh": info.get("yearHigh"),
        "yearLow": info.get("yearLow"),
    }