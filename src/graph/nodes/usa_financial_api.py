import requests
import os

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 불러오기
API_KEY = os.getenv("FINANCIAL_API_KEY")

def simplify_financial_data(data_list, fields, round_to_billion=True):
    """필요한 항목만 추출해서 깔끔하게 정리"""
    summary = []
    for item in data_list:
        row = {"fiscalYear": item.get("fiscalYear")}
        for field in fields:
            value = item.get(field, 0)
            try:
                row[field] = round(value / 1e8, 2) if round_to_billion else value
            except Exception:
                row[field] = None
        summary.append(row)
    return summary


def get_income_statement(symbol='AAPL', limit=3):
    print("손익계산서 Agent 호출")
    fields = ["revenue", "grossProfit", "operatingIncome", "netIncome", "eps", "epsDiluted"]
    url = f"https://financialmodelingprep.com/stable/income-statement?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return simplify_financial_data(response.json()[:limit], fields)
    return {"error": response.text}

def get_balance_sheet(symbol='AAPL', limit=3):
    print("대차대조표 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        print("API 호출 실패:", response.text)
        return {"error": response.text}

    try:
        data = response.json()[:limit]
        
        return simplify_financial_data(data, fields)  # 필요하면 정제된 원본도 반환
    except Exception as e:
        print("처리 중 오류:", str(e))
        return {"error": str(e)}


def get_cash_flow_statement(symbol='AAPL',limit=3):
    print("현금흐름표 Agent 호출")
    fields = [
        "netIncome",                        # 순이익
        "operatingCashFlow",               # 영업현금흐름
        "freeCashFlow",                    # 자유현금흐름
        "capitalExpenditure",              # 자본적 지출
        "netCashProvidedByFinancingActivities"  # 재무활동 현금흐름
    ]
    url = f"https://financialmodelingprep.com/stable/cash-flow-statement?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return simplify_financial_data(response.json()[:limit], fields)
    return {"error": response.text}

def get_financials(symbol='AAPL', limit=3):
    print("재무 보고서 Agent 호출")
    fields = [
        "symbol",       # 종목코드 (예: AAPL)
        "fiscalYear",   # 회계연도 (예: 2024)
        "period",       # 기간 (예: Q1, Q2, Q3, Q4, FY)
        "linkJson",     # JSON 형식 보고서 링크
        "linkXlsx"      # XLSX 형식 보고서 링크
    ]
    url = f"https://financialmodelingprep.com/stable/financial-reports-dates?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return simplify_financial_data(response.json()[:limit], fields)
    return {"error": response.text}

def get_key_metrics(symbol='AAPL', limit=3):
    print("주요지표 Agent 호출")
    fields = [
        "returnOnEquity",         # 자기자본이익률 (ROE)
        "freeCashFlowYield",      # FCF 수익률 (Free Cash Flow Yield)
        "evToEBITDA",             # EV/EBITDA (가치 대비 수익성)
        "earningsYield",          # 이익 수익률 (Inverse of P/E)
        "netDebtToEBITDA"         # 순부채/EBITDA (재무 레버리지)
    ]
    url = f"https://financialmodelingprep.com/stable/key-metrics?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return simplify_financial_data(response.json()[:limit], fields)
    return {"error": response.text}

def get_financial_ratios(symbol='AAPL', limit=3):
    print("재무 비율 Agent 호출")
    fields = [
        "grossProfitMargin",         # 매출총이익률
        "netProfitMargin",           # 순이익률
        "returnOnEquity",            # 자기자본이익률 (ROE) ← 다른 JSON에서 추출
        "priceToEarningsRatio",      # 주가수익비율 (PER)
        "freeCashFlowPerShare"       # 주당 자유현금흐름
    ]
    url = f"https://financialmodelingprep.com/stable/ratios?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return simplify_financial_data(response.json()[:limit], fields)
    return {"error": response.text}

def get_financial_scores(symbol='AAPL', limit=3):
    ###
    print("재무 점수 Agent 호출")
    fields = [
        "altmanZScore",       # 알트만 Z-Score: 파산 가능성 평가 지표
        "piotroskiScore",     # 피오트로스키 F-Score: 재무 건전성 9점 척도
        "ebit",               # 영업이익 (수익성 핵심 지표)
        "marketCap",          # 시가총액 (시장 가치 판단 지표)
        "totalLiabilities"    # 총부채 (재무 위험 평가용)
    ]

    url = f"https://financialmodelingprep.com/stable/financial-scores?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_enterprise_value(symbol='AAPL', limit=3):
    ###
    print("기업 가치 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/enterprise-values?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return simplify_financial_data(response.json()[:limit], fields)
    return {"error": response.text}

def get_income_statement_growth(symbol='AAPL', limit=3):
    print("손익 계산서 성장 Agent 호출")
    fields = [
        "growthRevenue",               # 매출 성장률
        "growthGrossProfit",           # 매출총이익 성장률
        "growthOperatingIncome",       # 영업이익 성장률
        "growthNetIncome",             # 순이익 성장률
        "growthEPS"                    # 주당순이익 성장률
    ]
    url = f"https://financialmodelingprep.com/stable/income-statement-growth?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return simplify_financial_data(response.json()[:limit], fields)
    return {"error": response.text}

def get_balance_sheet_growth(symbol='AAPL', limit=3):
    print("대차대조표 성장 Agent 호출")
    fields = [
        "growthTotalAssets",               # 총자산 성장률
        "growthTotalLiabilities",          # 총부채 성장률
        "growthTotalStockholdersEquity",   # 총자본 성장률
        "growthCashAndShortTermInvestments",  # 현금 및 단기투자 성장률
        "growthNetDebt"                    # 순부채 성장률
    ]
    url = f"https://financialmodelingprep.com/stable/balance-sheet-statement-growth?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return simplify_financial_data(response.json()[:limit], fields)
    return {"error": response.text}

def get_cash_flow_statement_growth(symbol='AAPL', limit=3):
    print("현금 흐름 보고서 성장 Agent 호출")
    fields = [
        "growthNetIncome",                  # 순이익 성장률
        "growthOperatingCashFlow",         # 영업활동 현금흐름 성장률
        "growthFreeCashFlow",              # 자유현금흐름 성장률
        "growthCapitalExpenditure",        # CAPEX 증가율
        "growthRevenue"                    # 매출 성장률 (※ 필요 시 따로 병합 필요)
    ]
    url = f"https://financialmodelingprep.com/stable/cash-flow-statement-growth?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return simplify_financial_data(response.json()[:limit], fields)
    return {"error": response.text}

def get_financials_growth(symbol='AAPL', limit=3):
    print("재무재표 성장 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/financial-growth?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return simplify_financial_data(response.json()[:limit], fields)
    return {"error": response.text}

