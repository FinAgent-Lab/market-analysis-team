"""Formatter functions for Alpha Vantage financial analysis results."""

from typing import Dict


def format_financial_analysis(analysis_data: Dict) -> str:
    """Format analysis data into readable text with focus on profitability and stability metrics."""
    output = []

    # Check if there was an error
    if "balance_sheet_error" in analysis_data:
        return f"Error retrieving balance sheet data: {analysis_data['balance_sheet_error']}"

    ticker = analysis_data.get("ticker", "Unknown")
    company_name = analysis_data.get("company_name", "")

    # Enhanced header with focus areas mentioned
    header = f"# Financial Statement Analysis for {company_name} (Ticker: {ticker})"
    subheader = "## Focus: Profitability & Financial Stability Metrics"
    output.append(header)
    output.append(subheader)

    # ===== 점수 대시보드 추가 =====
    analysis = analysis_data.get("analysis", {})
    financial_scores = analysis.get("financial_scores", {})

    if financial_scores and financial_scores.get('overall_score', 0) > 0:
        score_section = f"""
## 📊 **재무 건전성 종합 점수**

### 💯 **전체 평가**
- **종합 점수**: {financial_scores['overall_score']}/100점 ({financial_scores['overall_grade']})
- 🔥 **수익성**: {financial_scores['profitability_score']}/100점 ({financial_scores['profitability_grade']})
- 🛡️ **안정성**: {financial_scores['stability_score']}/100점 ({financial_scores['stability_grade']})

### 📋 **개별 지표 점수**
"""
        if 'individual_scores' in financial_scores:
            scores = financial_scores['individual_scores']
            values = financial_scores.get('metric_values', {})

            score_section += f"""
**수익성 지표:**
- ROE 점수: {scores.get('roe_score', 0)}/100점 (실제값: {values.get('roe', 'N/A')}%)
- ROA 점수: {scores.get('roa_score', 0)}/100점 (실제값: {values.get('roa', 'N/A')}%)
- 영업이익률 점수: {scores.get('operating_margin_score', 0)}/100점 (실제값: {values.get('operating_margin', 'N/A')}%)

**안정성 지표:**
- 유동비율 점수: {scores.get('current_ratio_score', 0)}/100점 (실제값: {values.get('current_ratio', 'N/A')})
- 부채비율 점수: {scores.get('debt_to_equity_score', 0)}/100점 (실제값: {values.get('debt_to_equity', 'N/A')})
"""

        score_section += f"""
### 🎯 **투자 관점**
{financial_scores.get('score_interpretation', '점수 해석 정보 없음')}

### 📚 **점수 해석 가이드**
- **90-100점 (A+)**: 최고 수준 - 매우 강력한 투자 후보
- **80-89점 (A)**: 우수한 수준 - 강력한 투자 후보
- **70-79점 (B+)**: 양호한 수준 - 고려할만한 투자 대상
- **60-69점 (B)**: 보통 수준 - 신중한 검토 필요
- **50-59점 (C+)**: 평균 이하 - 개선 사항 확인 필요
- **50점 미만 (C-D)**: 취약한 수준 - 주의 깊은 분석 필요

---
"""
        output.append(score_section)

    elif 'error' in financial_scores:
        output.append(f"\n⚠️ **점수 계산 오류**: {financial_scores['error']}\n")

    # ===== 점수 대시보드 끝 =====

    # Company profile information (기존 코드 그대로)
    profile = analysis_data.get("profile", {})
    if profile:
        output.append("\n### Company Profile")
        if "Sector" in profile and profile["Sector"]:
            output.append(f"- Sector: {profile['Sector']}")
        if "Industry" in profile and profile["Industry"]:
            output.append(f"- Industry: {profile['Industry']}")
        if "Description" in profile and profile["Description"]:
            output.append(f"- Description: {profile['Description'][:300]}...")

        if "MarketCapitalization" in profile:
            output.append(f"- Market Cap: {analysis.get('market_cap', 'No data')}")
        if "FullTimeEmployees" in profile:
            employees = profile.get("FullTimeEmployees")
            output.append(f"- Employees: {employees if employees else 'No data'}")

    # PROFITABILITY ANALYSIS - 점수 정보 추가
    output.append("\n### 📈 Profitability Analysis")

    # 수익성 점수 표시
    if financial_scores and 'profitability_score' in financial_scores:
        output.append(f"**📊 수익성 점수: {financial_scores['profitability_score']}/100점 ({financial_scores['profitability_grade']})**")
        output.append("")

    # Overall profitability assessment if available
    if "overall_profitability_assessment" in analysis:
        output.append(f"**Overall Assessment**: {analysis['overall_profitability_assessment']}")
        output.append("")

    # ROE metrics - 점수 추가
    if "roe" in analysis:
        output.append("#### Return on Equity (ROE)")
        output.append(f"- ROE: {analysis['roe']}")

        # 점수 정보 추가
        if financial_scores and 'individual_scores' in financial_scores:
            roe_score = financial_scores['individual_scores'].get('roe_score', 0)
            output.append(f"- **점수: {roe_score}/100점**")

        if "roe_evaluation" in analysis:
            output.append(f"- **Evaluation**: {analysis['roe_evaluation']}")
        output.append("")

    # ROA metrics - 점수 추가
    if "roa" in analysis:
        output.append("#### Return on Assets (ROA)")
        output.append(f"- ROA: {analysis['roa']}")

        # 점수 정보 추가
        if financial_scores and 'individual_scores' in financial_scores:
            roa_score = financial_scores['individual_scores'].get('roa_score', 0)
            output.append(f"- **점수: {roa_score}/100점**")

        if "roa_evaluation" in analysis:
            output.append(f"- **Evaluation**: {analysis['roa_evaluation']}")
        output.append("")

    # Margin analysis
    output.append("#### Margin Analysis")

    # Gross margin
    if "gross_margin" in analysis:
        output.append(f"- Gross Margin: {analysis['gross_margin']}")
        if "gross_margin_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['gross_margin_evaluation']}")

    # Operating margin - 점수 추가
    if "operating_margin" in analysis:
        output.append(f"- Operating Margin: {analysis['operating_margin']}")

        # 점수 정보 추가
        if financial_scores and 'individual_scores' in financial_scores:
            margin_score = financial_scores['individual_scores'].get('operating_margin_score', 0)
            output.append(f"  - **점수: {margin_score}/100점**")

        if "operating_margin_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['operating_margin_evaluation']}")

    # Net margin
    if "net_margin" in analysis:
        output.append(f"- Net Margin: {analysis['net_margin']}")
        if "net_margin_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['net_margin_evaluation']}")

    # EBITDA margin if available
    if "ebitda_margin" in analysis:
        output.append(f"- EBITDA Margin: {analysis['ebitda_margin']}")
        if "ebitda_margin_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['ebitda_margin_evaluation']}")

    output.append("")

    # Profitability Trends
    output.append("#### Profitability Trends")

    if "net_income_growth" in analysis:
        output.append(f"- Net Income Growth: {analysis['net_income_growth']}")
        if "net_income_growth_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['net_income_growth_evaluation']}")

    if "revenue_growth" in analysis:
        output.append(f"- Revenue Growth: {analysis['revenue_growth']}")
        if "revenue_growth_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['revenue_growth_evaluation']}")

    output.append("")

    # FINANCIAL STABILITY ANALYSIS - 점수 정보 추가
    output.append("\n### 🛡️ Financial Stability Analysis")

    # 안정성 점수 표시
    if financial_scores and 'stability_score' in financial_scores:
        output.append(f"**🛡️ 안정성 점수: {financial_scores['stability_score']}/100점 ({financial_scores['stability_grade']})**")
        output.append("")

    if "overall_stability_assessment" in analysis:
        output.append(f"**Overall Assessment**: {analysis['overall_stability_assessment']}")
        output.append("")

    # Liquidity Analysis
    output.append("#### Liquidity Analysis")

    # Current ratio - 점수 추가
    if "current_ratio" in analysis:
        output.append(f"- Current Ratio: {analysis['current_ratio']}")

        # 점수 정보 추가
        if financial_scores and 'individual_scores' in financial_scores:
            current_score = financial_scores['individual_scores'].get('current_ratio_score', 0)
            output.append(f"  - **점수: {current_score}/100점**")

        if "current_ratio_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['current_ratio_evaluation']}")

    if "quick_ratio" in analysis:
        output.append(f"- Quick Ratio (Acid Test): {analysis['quick_ratio']}")
        if "quick_ratio_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['quick_ratio_evaluation']}")

    if "cash_ratio" in analysis:
        output.append(f"- Cash Ratio: {analysis['cash_ratio']}")
        if "cash_ratio_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['cash_ratio_evaluation']}")

    output.append("")

    # Debt Analysis
    output.append("#### Debt & Leverage Analysis")

    # Debt-to-Equity - 점수 추가
    if "debt_to_equity" in analysis:
        output.append(f"- Debt-to-Equity Ratio: {analysis['debt_to_equity']}")

        # 점수 정보 추가
        if financial_scores and 'individual_scores' in financial_scores:
            debt_score = financial_scores['individual_scores'].get('debt_to_equity_score', 0)
            output.append(f"  - **점수: {debt_score}/100점**")

        if "debt_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['debt_evaluation']}")

    if "debt_to_assets" in analysis:
        output.append(f"- Debt-to-Assets Ratio: {analysis['debt_to_assets']}")
        if "debt_to_assets_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['debt_to_assets_evaluation']}")

    if "interest_coverage_ratio" in analysis:
        output.append(f"- Interest Coverage Ratio: {analysis['interest_coverage_ratio']}")
        if "interest_coverage_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['interest_coverage_evaluation']}")

    output.append("")

    # Cash Flow Analysis (기존 코드 그대로)
    output.append("#### Cash Flow Analysis")

    if "free_cash_flow" in analysis:
        output.append(f"- Free Cash Flow (FCF): {analysis['free_cash_flow']}")

    if "fcf_margin" in analysis:
        output.append(f"- FCF Margin: {analysis['fcf_margin']}")
        if "fcf_margin_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['fcf_margin_evaluation']}")

    if "fcf_to_net_income" in analysis:
        output.append(f"- FCF to Net Income Ratio: {analysis['fcf_to_net_income']}")
        if "cash_conversion_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['cash_conversion_evaluation']}")

    # 기존 Financial Statement Data 섹션들 (그대로 유지)
    output.append("\n### Key Financial Statement Data")

    # Income Statement metrics
    income_statement = analysis_data.get("income_statement", {}).get("annualReports", [])
    if income_statement and len(income_statement) > 0:
        recent = income_statement[0]
        period = recent.get("fiscalDateEnding", "N/A")
        output.append(f"#### Income Statement (Period: {period})")

        if "totalRevenue" in recent:
            output.append(f"- Revenue: {format_value(recent['totalRevenue'], prefix='$')}")
        if "grossProfit" in recent:
            output.append(f"- Gross Profit: {format_value(recent['grossProfit'], prefix='$')}")
        if "operatingIncome" in recent:
            output.append(f"- Operating Income: {format_value(recent['operatingIncome'], prefix='$')}")
        if "netIncome" in recent:
            output.append(f"- Net Income: {format_value(recent['netIncome'], prefix='$')}")
        if "ebitda" in recent:
            output.append(f"- EBITDA: {format_value(recent['ebitda'], prefix='$')}")

    # Balance Sheet metrics
    balance_sheet = analysis_data.get("balance_sheet", {}).get("annualReports", [])
    if balance_sheet and len(balance_sheet) > 0:
        recent = balance_sheet[0]
        period = recent.get("fiscalDateEnding", "N/A")
        output.append(f"\n#### Balance Sheet (Period: {period})")

        if "totalAssets" in recent:
            output.append(f"- Total Assets: {format_value(recent['totalAssets'], prefix='$')}")
        if "totalCurrentAssets" in recent:
            output.append(f"- Current Assets: {format_value(recent['totalCurrentAssets'], prefix='$')}")
        if "cash" in recent:
            output.append(f"- Cash & Equivalents: {format_value(recent['cash'], prefix='$')}")
        if "totalLiabilities" in recent:
            output.append(f"- Total Liabilities: {format_value(recent['totalLiabilities'], prefix='$')}")
        if "totalCurrentLiabilities" in recent:
            output.append(f"- Current Liabilities: {format_value(recent['totalCurrentLiabilities'], prefix='$')}")
        if "longTermDebt" in recent:
            output.append(f"- Long-Term Debt: {format_value(recent['longTermDebt'], prefix='$')}")
        if "totalShareholderEquity" in recent:
            output.append(f"- Total Shareholder Equity: {format_value(recent['totalShareholderEquity'], prefix='$')}")

    # Cash Flow metrics
    cash_flow = analysis_data.get("cash_flow", {}).get("annualReports", [])
    if cash_flow and len(cash_flow) > 0:
        recent = cash_flow[0]
        period = recent.get("fiscalDateEnding", "N/A")
        output.append(f"\n#### Cash Flow (Period: {period})")

        if "operatingCashflow" in recent:
            output.append(f"- Operating Cash Flow: {format_value(recent['operatingCashflow'], prefix='$')}")
        if "capitalExpenditures" in recent:
            output.append(f"- Capital Expenditures: {format_value(recent['capitalExpenditures'], prefix='$')}")
        if "cashflowFromInvestment" in recent:
            output.append(f"- Cash Flow from Investment: {format_value(recent['cashflowFromInvestment'], prefix='$')}")
        if "cashflowFromFinancing" in recent:
            output.append(f"- Cash Flow from Financing: {format_value(recent['cashflowFromFinancing'], prefix='$')}")
        if "dividendPayout" in recent:
            output.append(f"- Dividend Payout: {format_value(recent['dividendPayout'], prefix='$')}")

    # Summary and Investment Considerations (기존 코드 그대로 유지)
    output.append("\n### Summary and Investment Considerations")

    profitability_assessment = analysis.get("overall_profitability_assessment", "")
    stability_assessment = analysis.get("overall_stability_assessment", "")

    if profitability_assessment and stability_assessment:
        output.append("#### Key Strengths & Concerns")

        strengths = []
        concerns = []

        if "Exceptional" in profitability_assessment or "Strong" in profitability_assessment:
            strengths.append("High profitability metrics compared to industry benchmarks")
        elif "Weak" in profitability_assessment:
            concerns.append("Below-average profitability metrics that may impact investment returns")

        if "Exceptional" in stability_assessment or "Strong" in stability_assessment:
            strengths.append("Solid financial stability with strong balance sheet metrics")
        elif "Weak" in stability_assessment:
            concerns.append("Financial stability concerns that may increase investment risk")

        # 점수 기반 강점/약점 추가
        if financial_scores:
            overall_score = financial_scores.get('overall_score', 0)
            if overall_score >= 80:
                strengths.append(f"높은 재무 점수 ({overall_score}점)로 우수한 투자 후보")
            elif overall_score < 60:
                concerns.append(f"낮은 재무 점수 ({overall_score}점)로 신중한 검토 필요")

        if strengths:
            output.append("**Key Strengths:**")
            for strength in strengths:
                output.append(f"- {strength}")
            output.append("")

        if concerns:
            output.append("**Key Concerns:**")
            for concern in concerns:
                output.append(f"- {concern}")
            output.append("")

        output.append("#### Investment Considerations")
        output.append("This analysis focuses primarily on profitability and financial stability metrics. Investors should also consider:")
        output.append("- Future growth prospects and industry trends")
        output.append("- Competitive positioning and market share")
        output.append("- Management quality and strategic direction")
        output.append("- Valuation metrics relative to peers and historical ranges")
        output.append("- Macroeconomic factors that may impact the business")
        output.append("")
        output.append("*Note: This analysis represents a point-in-time assessment based on historical financial data and standard financial metrics.*")

    return "\n".join(output)


def format_value(value, prefix='', suffix='', decimal_places=2):
    """
    Safely format numerical values.
    Returns 'No data' for None or invalid values.
    """
    if value is None or value == "" or value == "None":
        return "No data"

    try:
        float_val = float(value)
        formatted = f"{float_val:,.{decimal_places}f}"
        return f"{prefix}{formatted}{suffix}"
    except (ValueError, TypeError):
        return "No data"