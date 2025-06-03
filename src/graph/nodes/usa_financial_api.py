import requests
import os

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 불러오기
API_KEY = os.getenv("FINANCIAL_API_KEY")


def get_income_statement(symbol='AAPL'):
    print("손익계산서 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/income-statement?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_balance_sheet(symbol='AAPL'):
    print("대차대조표 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        print("API 호출 실패:", response.text)
        return {"error": response.text}

    try:
        data = response.json()
        return data
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

def get_financials(symbol='AAPL'):
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

def get_financial_ratios(symbol='AAPL'):
    print("재무 비율 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/ratios?symbol={symbol}&apikey={API_KEY}"
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

def get_enterprise_value(symbol='AAPL'):
    ###
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
    print("대차대조표 성장 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/balance-sheet-statement-growth?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_cash_flow_statement_growth(symbol='AAPL'):
    print("현금 흐름 보고서 성장 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/cash-flow-statement-growth?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

def get_financials_growth(symbol='AAPL'):
    print("재무재표 성장 Agent 호출")
    url = f"https://financialmodelingprep.com/stable/financial-growth?symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    return {"error": response.text}

