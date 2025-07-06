"""Analysis functions for financial stability metrics from Alpha Vantage financial data."""

from typing import Dict


def calculate_overall_stability_assessment(analysis: Dict) -> Dict:
    """Calculate the overall stability assessment based on various factors."""
    try:
        stability_factors = []

        # Current ratio assessment
        if "current_ratio_evaluation" in analysis:
            if (
                "Exceptional" in analysis["current_ratio_evaluation"]
                or "Excellent" in analysis["current_ratio_evaluation"]
            ):
                stability_factors.append(2)  # Strong positive
            elif (
                "Good" in analysis["current_ratio_evaluation"]
                or "Adequate" in analysis["current_ratio_evaluation"]
            ):
                stability_factors.append(1)  # Positive
            elif "Borderline" in analysis["current_ratio_evaluation"]:
                stability_factors.append(0)  # Neutral
            elif "risk" in analysis["current_ratio_evaluation"].lower():
                stability_factors.append(-1)  # Negative

        # Debt evaluation assessment
        if "debt_evaluation" in analysis:
            if (
                "Minimal" in analysis["debt_evaluation"]
                or "Low" in analysis["debt_evaluation"]
            ):
                stability_factors.append(2)  # Strong positive
            elif "Moderate" in analysis["debt_evaluation"]:
                stability_factors.append(1)  # Positive
            elif "Significant" in analysis["debt_evaluation"]:
                stability_factors.append(0)  # Neutral
            elif (
                "High" in analysis["debt_evaluation"]
                or "Very high" in analysis["debt_evaluation"]
            ):
                stability_factors.append(-1)  # Negative

        # Interest coverage assessment if available
        if "interest_coverage_evaluation" in analysis:
            if (
                "Exceptional" in analysis["interest_coverage_evaluation"]
                or "Strong" in analysis["interest_coverage_evaluation"]
            ):
                stability_factors.append(2)  # Strong positive
            elif "Good" in analysis["interest_coverage_evaluation"]:
                stability_factors.append(1)  # Positive
            elif "Adequate" in analysis["interest_coverage_evaluation"]:
                stability_factors.append(0)  # Neutral
            elif "Limited" in analysis["interest_coverage_evaluation"]:
                stability_factors.append(-1)  # Negative

        # Cash ratio assessment if available
        if "cash_ratio_evaluation" in analysis:
            if (
                "Exceptional" in analysis["cash_ratio_evaluation"]
                or "Strong" in analysis["cash_ratio_evaluation"]
            ):
                stability_factors.append(2)  # Strong positive
            elif "Adequate" in analysis["cash_ratio_evaluation"]:
                stability_factors.append(1)  # Positive
            elif "Limited" in analysis["cash_ratio_evaluation"]:
                stability_factors.append(-1)  # Negative

        # FCF assessment if available
        if "fcf_margin_evaluation" in analysis:
            if (
                "Exceptional" in analysis["fcf_margin_evaluation"]
                or "Strong" in analysis["fcf_margin_evaluation"]
            ):
                stability_factors.append(2)  # Strong positive
            elif "Good" in analysis["fcf_margin_evaluation"]:
                stability_factors.append(1)  # Positive
            elif "Positive" in analysis["fcf_margin_evaluation"]:
                stability_factors.append(0)  # Neutral
            elif "Negative" in analysis["fcf_margin_evaluation"]:
                stability_factors.append(-1)  # Negative

        # Calculate overall stability score if we have factors
        if stability_factors:
            avg_score = sum(stability_factors) / len(stability_factors)

            # Provide overall stability evaluation
            if avg_score > 1.5:
                analysis["overall_stability_assessment"] = (
                    "Exceptional financial stability - Fortress balance sheet"
                )
            elif avg_score > 0.75:
                analysis["overall_stability_assessment"] = (
                    "Strong financial stability - Well-positioned to weather adverse conditions"
                )
            elif avg_score > 0:
                analysis["overall_stability_assessment"] = (
                    "Good financial stability - Reasonable risk profile"
                )
            elif avg_score > -0.5:
                analysis["overall_stability_assessment"] = (
                    "Adequate financial stability - Some potential concerns"
                )
            else:
                analysis["overall_stability_assessment"] = (
                    "Weak financial stability - Significant risk factors present"
                )

        return analysis

    except Exception as e:
        analysis["overall_stability_assessment_error"] = str(e)
        return analysis


def analyze_stability_from_balance_sheet(
    api_wrapper, balance_sheet_data: Dict, income_statement_data: Dict = None
) -> Dict:
    """Analyze financial stability metrics from balance sheet data."""
    analysis = {}

    if not balance_sheet_data or "annualReports" not in balance_sheet_data:
        return analysis

    annual_reports = balance_sheet_data.get("annualReports", [])
    if not annual_reports:
        return analysis

    try:
        recent = annual_reports[0]

        # Extract basic metrics - safely convert values
        total_assets = api_wrapper.safe_float_or_empty(recent.get("totalAssets"))
        total_liabilities = api_wrapper.safe_float_or_empty(
            recent.get("totalLiabilities")
        )
        total_equity = api_wrapper.safe_float_or_empty(
            recent.get("totalShareholderEquity")
        )

        # Add basic metrics
        analysis["total_assets"] = api_wrapper.format_financial_value(total_assets)
        analysis["total_liabilities"] = api_wrapper.format_financial_value(
            total_liabilities
        )
        analysis["total_equity"] = api_wrapper.format_financial_value(total_equity)

        # Enhanced Liquidity Analysis
        current_assets = api_wrapper.safe_float_or_empty(
            recent.get("totalCurrentAssets")
        )
        current_liabilities = api_wrapper.safe_float_or_empty(
            recent.get("totalCurrentLiabilities")
        )
        cash = api_wrapper.safe_float_or_empty(recent.get("cash"))
        cash_equivalents = api_wrapper.safe_float_or_empty(
            recent.get("cashAndShortTermInvestments", 0)
        )
        inventory = api_wrapper.safe_float_or_empty(recent.get("inventory", 0))

        analysis["current_assets"] = api_wrapper.format_financial_value(current_assets)
        analysis["current_liabilities"] = api_wrapper.format_financial_value(
            current_liabilities
        )
        analysis["cash_and_equivalents"] = api_wrapper.format_financial_value(
            cash if cash is not None else cash_equivalents
        )

        # Current Ratio (Stability)
        if (
            current_liabilities is not None
            and current_assets is not None
            and current_liabilities > 0
        ):
            current_ratio = current_assets / current_liabilities
            analysis["current_ratio"] = f"{current_ratio:.2f}"

            # Enhanced current ratio evaluation
            if current_ratio > 3:
                analysis["current_ratio_evaluation"] = (
                    "Exceptional liquidity - Very conservative"
                )
            elif current_ratio > 2:
                analysis["current_ratio_evaluation"] = (
                    "Excellent liquidity - Strong financial stability"
                )
            elif current_ratio > 1.5:
                analysis["current_ratio_evaluation"] = (
                    "Good liquidity - Solid short-term stability"
                )
            elif current_ratio > 1:
                analysis["current_ratio_evaluation"] = (
                    "Adequate liquidity - Minimal short-term risk"
                )
            elif current_ratio > 0.8:
                analysis["current_ratio_evaluation"] = (
                    "Borderline liquidity - Potential short-term concerns"
                )
            else:
                analysis["current_ratio_evaluation"] = (
                    "Liquidity risk - Potential short-term obligations issues"
                )
        else:
            analysis["current_ratio"] = "No data"
            analysis["current_ratio_evaluation"] = (
                "Unable to evaluate liquidity due to insufficient data"
            )

        # Quick Ratio (Acid Test) - Stricter liquidity test
        if (
            current_liabilities is not None
            and current_liabilities > 0
            and current_assets is not None
            and inventory is not None
        ):
            quick_ratio = (current_assets - inventory) / current_liabilities
            analysis["quick_ratio"] = f"{quick_ratio:.2f}"

            # Quick ratio evaluation
            if quick_ratio > 1.5:
                analysis["quick_ratio_evaluation"] = "Strong immediate liquidity"
            elif quick_ratio > 1:
                analysis["quick_ratio_evaluation"] = "Good immediate liquidity"
            elif quick_ratio > 0.7:
                analysis["quick_ratio_evaluation"] = "Adequate immediate liquidity"
            else:
                analysis["quick_ratio_evaluation"] = (
                    "Potential immediate liquidity concerns"
                )
        else:
            analysis["quick_ratio"] = "No data"
            analysis["quick_ratio_evaluation"] = (
                "Unable to evaluate immediate liquidity due to insufficient data"
            )

        # Cash Ratio - Most conservative liquidity test
        if (
            current_liabilities is not None
            and current_liabilities > 0
            and cash is not None
        ):
            cash_ratio = cash / current_liabilities
            analysis["cash_ratio"] = f"{cash_ratio:.2f}"

            # Cash ratio evaluation
            if cash_ratio > 1:
                analysis["cash_ratio_evaluation"] = (
                    "Exceptional cash liquidity - Highly conservative"
                )
            elif cash_ratio > 0.5:
                analysis["cash_ratio_evaluation"] = "Strong cash position"
            elif cash_ratio > 0.2:
                analysis["cash_ratio_evaluation"] = "Adequate cash reserves"
            else:
                analysis["cash_ratio_evaluation"] = "Limited immediate cash available"
        else:
            analysis["cash_ratio"] = "No data"
            analysis["cash_ratio_evaluation"] = (
                "Unable to evaluate cash position due to insufficient data"
            )

        # Debt Analysis
        long_term_debt = api_wrapper.safe_float_or_empty(recent.get("longTermDebt"))
        if long_term_debt is not None:
            analysis["long_term_debt"] = api_wrapper.format_financial_value(
                long_term_debt
            )

        # Debt-to-Equity (Leverage & Stability)
        if (
            total_equity is not None
            and total_liabilities is not None
            and total_equity > 0
        ):
            debt_to_equity = total_liabilities / total_equity
            analysis["debt_to_equity"] = f"{debt_to_equity:.2f}"

            # Enhanced debt-to-equity evaluation with industry context
            if debt_to_equity < 0.3:
                analysis["debt_evaluation"] = (
                    "Minimal leverage - Very conservative capital structure"
                )
            elif debt_to_equity < 0.5:
                analysis["debt_evaluation"] = (
                    "Low leverage - Conservative capital structure"
                )
            elif debt_to_equity < 1.0:
                analysis["debt_evaluation"] = (
                    "Moderate leverage - Balanced capital structure"
                )
            elif debt_to_equity < 1.5:
                analysis["debt_evaluation"] = (
                    "Significant leverage - More aggressive capital structure"
                )
            elif debt_to_equity < 2.0:
                analysis["debt_evaluation"] = (
                    "High leverage - Aggressive capital structure with elevated risk"
                )
            else:
                analysis["debt_evaluation"] = (
                    "Very high leverage - Potential financial distress risk"
                )
        else:
            analysis["debt_to_equity"] = "No data"
            analysis["debt_evaluation"] = (
                "Unable to evaluate debt structure due to insufficient data"
            )

        # Debt-to-Assets Ratio (Financial Risk)
        if (
            total_assets is not None
            and total_assets > 0
            and total_liabilities is not None
        ):
            debt_to_assets = total_liabilities / total_assets
            analysis["debt_to_assets"] = f"{debt_to_assets:.2f}"

            # Debt-to-assets evaluation
            if debt_to_assets < 0.2:
                analysis["debt_to_assets_evaluation"] = "Very low financial risk"
            elif debt_to_assets < 0.4:
                analysis["debt_to_assets_evaluation"] = "Low financial risk"
            elif debt_to_assets < 0.6:
                analysis["debt_to_assets_evaluation"] = "Moderate financial risk"
            elif debt_to_assets < 0.8:
                analysis["debt_to_assets_evaluation"] = "High financial risk"
            else:
                analysis["debt_to_assets_evaluation"] = (
                    "Very high financial risk - Potential solvency concerns"
                )
        else:
            analysis["debt_to_assets"] = "No data"
            analysis["debt_to_assets_evaluation"] = (
                "Unable to evaluate financial risk due to insufficient data"
            )

        # Interest Coverage Ratio (if income statement data available)
        if income_statement_data and "annualReports" in income_statement_data:
            income_reports = income_statement_data.get("annualReports", [])

            if income_reports:
                recent_income = income_reports[0]
                operating_income = api_wrapper.safe_float_or_empty(
                    recent_income.get("operatingIncome")
                )
                interest_expense = api_wrapper.safe_float_or_empty(
                    recent_income.get("interestExpense")
                )

                if (
                    operating_income is not None
                    and interest_expense is not None
                    and interest_expense != 0
                ):
                    interest_coverage = operating_income / abs(interest_expense)
                    analysis["interest_coverage_ratio"] = f"{interest_coverage:.2f}"

                    # Interest coverage evaluation
                    if interest_coverage > 8:
                        analysis["interest_coverage_evaluation"] = (
                            "Exceptional debt service capability"
                        )
                    elif interest_coverage > 5:
                        analysis["interest_coverage_evaluation"] = (
                            "Strong debt service capability"
                        )
                    elif interest_coverage > 3:
                        analysis["interest_coverage_evaluation"] = (
                            "Good debt service capability"
                        )
                    elif interest_coverage > 1.5:
                        analysis["interest_coverage_evaluation"] = (
                            "Adequate debt service capability"
                        )
                    else:
                        analysis["interest_coverage_evaluation"] = (
                            "Limited debt service capability - Potential risk"
                        )
                else:
                    analysis["interest_coverage_ratio"] = "No data"
                    analysis["interest_coverage_evaluation"] = (
                        "Unable to evaluate debt service capability due to insufficient data"
                    )

    except Exception as e:
        analysis["balance_sheet_stability_analysis_error"] = str(e)

    return analysis


def analyze_stability_from_cash_flow(
    api_wrapper, cash_flow_data: Dict, income_statement_data: Dict = None
) -> Dict:
    """Analyze stability metrics from cash flow data."""
    analysis = {}

    if not cash_flow_data or "annualReports" not in cash_flow_data:
        return analysis

    annual_reports = cash_flow_data.get("annualReports", [])
    if not annual_reports:
        return analysis

    try:
        recent = annual_reports[0]

        # Extract key cash flow metrics
        operating_cash_flow = api_wrapper.safe_float_or_empty(
            recent.get("operatingCashflow")
        )
        capital_expenditures = api_wrapper.safe_float_or_empty(
            recent.get("capitalExpenditures")
        )

        # Add basic metrics
        if operating_cash_flow is not None:
            analysis["operating_cash_flow"] = api_wrapper.format_financial_value(
                operating_cash_flow
            )
        if capital_expenditures is not None:
            analysis["capital_expenditures"] = api_wrapper.format_financial_value(
                capital_expenditures
            )

        # Free Cash Flow - Important stability metric
        if operating_cash_flow is not None and capital_expenditures is not None:
            free_cash_flow = operating_cash_flow - abs(capital_expenditures)
            analysis["free_cash_flow"] = api_wrapper.format_financial_value(
                free_cash_flow
            )

            # Get recent net income for comparison if income statement data available
            recent_net_income = None
            recent_revenue = None

            if income_statement_data and "annualReports" in income_statement_data:
                income_reports = income_statement_data.get("annualReports", [])

                if income_reports:
                    recent_income = income_reports[0]
                    recent_net_income = api_wrapper.safe_float_or_empty(
                        recent_income.get("netIncome")
                    )
                    recent_revenue = api_wrapper.safe_float_or_empty(
                        recent_income.get("totalRevenue")
                    )

            # FCF to Net Income Ratio - Cash Quality Indicator
            if recent_net_income is not None and recent_net_income != 0:
                fcf_to_net_income = free_cash_flow / recent_net_income
                analysis["fcf_to_net_income"] = f"{fcf_to_net_income:.2f}"

                # Evaluation of cash conversion quality
                if fcf_to_net_income > 1.5:
                    analysis["cash_conversion_evaluation"] = (
                        "Exceptional cash conversion - Very high quality earnings"
                    )
                elif fcf_to_net_income > 1.2:
                    analysis["cash_conversion_evaluation"] = (
                        "Strong cash conversion - High quality earnings"
                    )
                elif fcf_to_net_income > 0.9:
                    analysis["cash_conversion_evaluation"] = (
                        "Good cash conversion - Quality earnings"
                    )
                elif fcf_to_net_income > 0.6:
                    analysis["cash_conversion_evaluation"] = "Adequate cash conversion"
                else:
                    analysis["cash_conversion_evaluation"] = (
                        "Poor cash conversion - Potential earnings quality concerns"
                    )

            # FCF Margin - if revenue data available
            if recent_revenue is not None and recent_revenue > 0:
                fcf_margin = (free_cash_flow / recent_revenue) * 100
                analysis["fcf_margin"] = f"{fcf_margin:.2f}%"

                # FCF margin evaluation
                if fcf_margin > 15:
                    analysis["fcf_margin_evaluation"] = (
                        "Exceptional FCF margin - Highly cash generative business"
                    )
                elif fcf_margin > 10:
                    analysis["fcf_margin_evaluation"] = (
                        "Strong FCF margin - Very cash generative business"
                    )
                elif fcf_margin > 5:
                    analysis["fcf_margin_evaluation"] = (
                        "Good FCF margin - Cash generative business"
                    )
                elif fcf_margin > 0:
                    analysis["fcf_margin_evaluation"] = "Positive FCF margin"
                else:
                    analysis["fcf_margin_evaluation"] = (
                        "Negative FCF margin - Cash burn concerns"
                    )

    except Exception as e:
        analysis["cash_flow_stability_analysis_error"] = str(e)

    return analysis
