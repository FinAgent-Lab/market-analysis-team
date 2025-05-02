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

    # Company profile information
    profile = analysis_data.get("profile", {})
    if profile:
        output.append("\n## Company Profile")
        # Always check if keys exist and have values
        if "Sector" in profile and profile["Sector"]:
            output.append(f"- Sector: {profile['Sector']}")
        if "Industry" in profile and profile["Industry"]:
            output.append(f"- Industry: {profile['Industry']}")
        if "Description" in profile and profile["Description"]:
            output.append(f"- Description: {profile['Description'][:300]}...")

        # Always use safe_format for market cap and employees
        if "MarketCapitalization" in profile:
            output.append(f"- Market Cap: {analysis_data.get('analysis', {}).get('market_cap', 'No data')}")
        if "FullTimeEmployees" in profile:
            employees = profile.get("FullTimeEmployees")
            output.append(f"- Employees: {employees if employees else 'No data'}")

    # PROFITABILITY ANALYSIS - Focus Area #1
    output.append("\n## 📈 Profitability Analysis")

    # Extract analysis data
    analysis = analysis_data.get("analysis", {})

    # Overall profitability assessment if available
    if "overall_profitability_assessment" in analysis:
        output.append(f"**Overall Assessment**: {analysis['overall_profitability_assessment']}")
        output.append("")  # Add empty line for readability

    # ROE metrics - Key profitability indicator
    if "roe" in analysis:
        output.append("### Return on Equity (ROE)")
        output.append(f"- ROE: {analysis['roe']}")
        if "roe_evaluation" in analysis:
            output.append(f"- **Evaluation**: {analysis['roe_evaluation']}")
        output.append("")  # Add empty line for readability

    # ROA metrics
    if "roa" in analysis:
        output.append("### Return on Assets (ROA)")
        output.append(f"- ROA: {analysis['roa']}")
        if "roa_evaluation" in analysis:
            output.append(f"- **Evaluation**: {analysis['roa_evaluation']}")
        output.append("")  # Add empty line for readability

    # Margin analysis
    output.append("### Margin Analysis")

    # Gross margin
    if "gross_margin" in analysis:
        output.append(f"- Gross Margin: {analysis['gross_margin']}")
        if "gross_margin_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['gross_margin_evaluation']}")

    # Operating margin
    if "operating_margin" in analysis:
        output.append(f"- Operating Margin: {analysis['operating_margin']}")
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

    output.append("")  # Add empty line for readability

    # Profitability Trends
    output.append("### Profitability Trends")

    # Net income growth
    if "net_income_growth" in analysis:
        output.append(f"- Net Income Growth: {analysis['net_income_growth']}")
        if "net_income_growth_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['net_income_growth_evaluation']}")

    # Revenue growth (included for context)
    if "revenue_growth" in analysis:
        output.append(f"- Revenue Growth: {analysis['revenue_growth']}")
        if "revenue_growth_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['revenue_growth_evaluation']}")

    output.append("")  # Add empty line for readability

    # FINANCIAL STABILITY ANALYSIS - Focus Area #2
    output.append("\n## 🛡️ Financial Stability Analysis")

    # Overall stability assessment if available
    if "overall_stability_assessment" in analysis:
        output.append(f"**Overall Assessment**: {analysis['overall_stability_assessment']}")
        output.append("")  # Add empty line for readability

    # Liquidity Analysis
    output.append("### Liquidity Analysis")

    # Current ratio
    if "current_ratio" in analysis:
        output.append(f"- Current Ratio: {analysis['current_ratio']}")
        if "current_ratio_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['current_ratio_evaluation']}")

    # Quick ratio
    if "quick_ratio" in analysis:
        output.append(f"- Quick Ratio (Acid Test): {analysis['quick_ratio']}")
        if "quick_ratio_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['quick_ratio_evaluation']}")

    # Cash ratio
    if "cash_ratio" in analysis:
        output.append(f"- Cash Ratio: {analysis['cash_ratio']}")
        if "cash_ratio_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['cash_ratio_evaluation']}")

    output.append("")  # Add empty line for readability

    # Debt Analysis
    output.append("### Debt & Leverage Analysis")

    # Debt-to-Equity
    if "debt_to_equity" in analysis:
        output.append(f"- Debt-to-Equity Ratio: {analysis['debt_to_equity']}")
        if "debt_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['debt_evaluation']}")

    # Debt-to-Assets
    if "debt_to_assets" in analysis:
        output.append(f"- Debt-to-Assets Ratio: {analysis['debt_to_assets']}")
        if "debt_to_assets_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['debt_to_assets_evaluation']}")

    # Interest Coverage
    if "interest_coverage_ratio" in analysis:
        output.append(f"- Interest Coverage Ratio: {analysis['interest_coverage_ratio']}")
        if "interest_coverage_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['interest_coverage_evaluation']}")

    output.append("")  # Add empty line for readability

    # Cash Flow Analysis
    output.append("### Cash Flow Analysis")

    # Free Cash Flow
    if "free_cash_flow" in analysis:
        output.append(f"- Free Cash Flow (FCF): {analysis['free_cash_flow']}")

    # FCF Margin
    if "fcf_margin" in analysis:
        output.append(f"- FCF Margin: {analysis['fcf_margin']}")
        if "fcf_margin_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['fcf_margin_evaluation']}")

    # FCF to Net Income Ratio (Cash conversion quality)
    if "fcf_to_net_income" in analysis:
        output.append(f"- FCF to Net Income Ratio: {analysis['fcf_to_net_income']}")
        if "cash_conversion_evaluation" in analysis:
            output.append(f"  - **Evaluation**: {analysis['cash_conversion_evaluation']}")

    # Financial Statement Data - Add basic metrics for reference
    output.append("\n## Key Financial Statement Data")

    # Income Statement metrics
    income_statement = analysis_data.get("income_statement", {}).get("annualReports", [])
    if income_statement and len(income_statement) > 0:
        recent = income_statement[0]
        period = recent.get("fiscalDateEnding", "N/A")
        output.append(f"### Income Statement (Period: {period})")

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
        output.append(f"\n### Balance Sheet (Period: {period})")

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
        output.append(f"\n### Cash Flow (Period: {period})")

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

    # Summary and Investment Considerations
    output.append("\n## Summary and Investment Considerations")

    # Create summary based on profitability and stability assessments
    profitability_assessment = analysis.get("overall_profitability_assessment", "")
    stability_assessment = analysis.get("overall_stability_assessment", "")

    if profitability_assessment and stability_assessment:
        output.append("### Key Strengths & Concerns")

        # Generate strengths list
        strengths = []
        concerns = []

        # Check profitability metrics for strengths and concerns
        if "Exceptional" in profitability_assessment or "Strong" in profitability_assessment:
            strengths.append("High profitability metrics compared to industry benchmarks")
        elif "Weak" in profitability_assessment:
            concerns.append("Below-average profitability metrics that may impact investment returns")

        # Check stability metrics for strengths and concerns
        if "Exceptional" in stability_assessment or "Strong" in stability_assessment:
            strengths.append("Solid financial stability with strong balance sheet metrics")
        elif "Weak" in stability_assessment:
            concerns.append("Financial stability concerns that may increase investment risk")

        # Check specific metrics for additional insights
        if "roe_evaluation" in analysis and "Excellent" in analysis["roe_evaluation"]:
            strengths.append("Strong return on equity indicating efficient use of shareholder capital")

        if "operating_margin_evaluation" in analysis and "Elite" in analysis["operating_margin_evaluation"]:
            strengths.append("Industry-leading operating margins demonstrating operational excellence")

        if "debt_evaluation" in analysis:
            if "Very high" in analysis["debt_evaluation"] or "High" in analysis["debt_evaluation"]:
                concerns.append("High leverage that may increase financial risk during economic downturns")
            elif "Minimal" in analysis["debt_evaluation"] or "Low" in analysis["debt_evaluation"]:
                strengths.append("Conservative debt levels providing financial flexibility")

        if "current_ratio_evaluation" in analysis and "risk" in analysis["current_ratio_evaluation"].lower():
            concerns.append("Liquidity concerns that may impact short-term financial obligations")

        if "fcf_margin_evaluation" in analysis:
            if "Exceptional" in analysis["fcf_margin_evaluation"] or "Strong" in analysis["fcf_margin_evaluation"]:
                strengths.append("Excellent cash generation capabilities supporting future growth and shareholder returns")
            elif "Negative" in analysis["fcf_margin_evaluation"]:
                concerns.append("Negative free cash flow indicating potential cash burn issues")

        # Output strengths
        if strengths:
            output.append("**Key Strengths:**")
            for strength in strengths:
                output.append(f"- {strength}")
            output.append("")  # Add empty line for readability

        # Output concerns
        if concerns:
            output.append("**Key Concerns:**")
            for concern in concerns:
                output.append(f"- {concern}")
            output.append("")  # Add empty line for readability

        # Final notes
        output.append("### Investment Considerations")
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