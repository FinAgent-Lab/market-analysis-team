"""Alpha Vantage API wrapper and financial analysis package."""

from .alpha_vantage_client import AlphaVantageAPIWrapper
from .alpha_vantage_profitability import (
    analyze_profitability_from_profile,
    analyze_profitability_from_income_statement,
    calculate_overall_profitability_assessment,
)
from .alpha_vantage_stability import (
    analyze_stability_from_balance_sheet,
    analyze_stability_from_cash_flow,
    calculate_overall_stability_assessment,
)
from .alpha_vantage_formatters import format_financial_analysis
from .alpha_vantage_scoring import FinancialScoringSystem


# Integrate analysis functions
def analyze_financial_data(api_wrapper, data: dict) -> dict:
    """Analyze financial statement data with focus on profitability and stability."""
    analysis = {}

    # Extract components
    profile = data.get("profile", {})
    balance_sheet_data = data.get("balance_sheet", {})
    income_statement_data = data.get("income_statement", {})
    cash_flow_data = data.get("cash_flow", {})

    # Basic profile info
    if profile:
        if "Sector" in profile:
            analysis["sector"] = profile["Sector"]
        if "Industry" in profile:
            analysis["industry"] = profile["Industry"]
        if "MarketCapitalization" in profile:
            market_cap = api_wrapper.safe_float_or_empty(
                profile["MarketCapitalization"]
            )
            analysis["market_cap"] = api_wrapper.format_financial_value(market_cap)
        if "FullTimeEmployees" in profile:
            analysis["employees"] = (
                profile["FullTimeEmployees"]
                if profile["FullTimeEmployees"]
                else "No data"
            )

        # Basic financials from overview
        if "EPS" in profile:
            eps = api_wrapper.safe_float_or_empty(profile["EPS"])
            analysis["eps"] = api_wrapper.format_financial_value(eps)
        if "PERatio" in profile:
            pe_ratio = api_wrapper.safe_float_or_empty(profile["PERatio"])
            analysis["pe_ratio"] = api_wrapper.format_financial_value(
                pe_ratio, include_dollar=False
            )
        if "PEGRatio" in profile:
            peg_ratio = api_wrapper.safe_float_or_empty(profile["PEGRatio"])
            analysis["peg_ratio"] = api_wrapper.format_financial_value(
                peg_ratio, include_dollar=False
            )
        if "DividendYield" in profile:
            div_yield = api_wrapper.safe_float_or_empty(profile["DividendYield"])
            if div_yield is not None:
                analysis["dividend_yield"] = api_wrapper.format_financial_value(
                    div_yield * 100, include_dollar=False, include_percent=True
                )
            else:
                analysis["dividend_yield"] = "No data"
        if "PriceToBookRatio" in profile:
            pb_ratio = api_wrapper.safe_float_or_empty(profile["PriceToBookRatio"])
            analysis["pb_ratio"] = api_wrapper.format_financial_value(
                pb_ratio, include_dollar=False
            )

    # Run profitability analysis
    if profile:
        profitability_metrics = analyze_profitability_from_profile(api_wrapper, profile)
        analysis.update(profitability_metrics)

    if income_statement_data:
        income_statement_metrics = analyze_profitability_from_income_statement(
            api_wrapper, income_statement_data
        )
        analysis.update(income_statement_metrics)

    # Run stability analysis
    if balance_sheet_data:
        balance_sheet_metrics = analyze_stability_from_balance_sheet(
            api_wrapper, balance_sheet_data, income_statement_data
        )
        analysis.update(balance_sheet_metrics)

    if cash_flow_data:
        cash_flow_metrics = analyze_stability_from_cash_flow(
            api_wrapper, cash_flow_data, income_statement_data
        )
        analysis.update(cash_flow_metrics)

    # Calculate overall assessments
    analysis = calculate_overall_profitability_assessment(analysis)
    analysis = calculate_overall_stability_assessment(analysis)

    # ===== 간단한 점수화 시스템 통합 =====
    try:
        # 점수화 시스템 초기화
        scoring_system = FinancialScoringSystem()

        # 기존 분석 결과에서 점수 계산
        financial_scores = scoring_system.calculate_financial_scores(analysis)

        # 점수 정보를 analysis에 추가
        analysis["financial_scores"] = financial_scores

        # 점수 요약도 추가 (formatter에서 사용)
        analysis["score_summary"] = scoring_system.format_score_summary(
            financial_scores
        )

    except Exception as e:
        print(f"Error in scoring calculation: {e}")
        # 점수 계산 실패 시에도 기존 분석은 유지
        analysis["financial_scores"] = {
            "overall_score": 0,
            "overall_grade": "N/A",
            "profitability_score": 0,
            "profitability_grade": "N/A",
            "stability_score": 0,
            "stability_grade": "N/A",
            "error": str(e),
        }
        analysis["score_summary"] = "점수 계산을 완료할 수 없습니다."
    # ===== 점수화 시스템 통합 끝 =====

    return analysis


__all__ = [
    "AlphaVantageAPIWrapper",
    "analyze_financial_data",
    "format_financial_analysis",
    "FinancialScoringSystem",
]
