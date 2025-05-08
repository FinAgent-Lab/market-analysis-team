"""Analysis functions for profitability metrics from Alpha Vantage financial data."""

from typing import Dict


def analyze_profitability_from_profile(api_wrapper, profile: Dict) -> Dict:
    """Analyze profitability metrics from company profile data."""
    analysis = {}

    try:
        # Return on Equity (ROE)
        if "ReturnOnEquityTTM" in profile:
            roe = api_wrapper.safe_float_or_empty(profile["ReturnOnEquityTTM"])
            if roe is not None:
                roe_value = roe * 100
                analysis["roe"] = api_wrapper.format_financial_value(
                    roe_value, include_dollar=False, include_percent=True
                )

                # Enhanced ROE evaluation with industry benchmarks
                if roe_value > 20:
                    analysis["roe_evaluation"] = (
                        "Exceptional ROE - Top tier profitability"
                    )
                elif roe_value > 15:
                    analysis["roe_evaluation"] = "Excellent ROE - Strong profitability"
                elif roe_value > 10:
                    analysis["roe_evaluation"] = (
                        "Good ROE - Above average profitability"
                    )
                elif roe_value > 5:
                    analysis["roe_evaluation"] = "Average ROE - Moderate profitability"
                else:
                    analysis["roe_evaluation"] = (
                        "Below average ROE - May indicate profitability concerns"
                    )
            else:
                analysis["roe"] = "No data"
                analysis["roe_evaluation"] = (
                    "Unable to evaluate ROE due to insufficient data"
                )

        # Return on Assets (ROA)
        if "ReturnOnAssetsTTM" in profile:
            roa = api_wrapper.safe_float_or_empty(profile["ReturnOnAssetsTTM"])
            if roa is not None:
                roa_value = roa * 100
                analysis["roa"] = api_wrapper.format_financial_value(
                    roa_value, include_dollar=False, include_percent=True
                )

                # Enhanced ROA evaluation
                if roa_value > 10:
                    analysis["roa_evaluation"] = "Excellent asset utilization"
                elif roa_value > 7:
                    analysis["roa_evaluation"] = "Strong asset utilization"
                elif roa_value > 5:
                    analysis["roa_evaluation"] = "Good asset utilization"
                elif roa_value > 3:
                    analysis["roa_evaluation"] = "Average asset utilization"
                else:
                    analysis["roa_evaluation"] = "Inefficient asset utilization"
            else:
                analysis["roa"] = "No data"
                analysis["roa_evaluation"] = (
                    "Unable to evaluate ROA due to insufficient data"
                )

        # Operating Margin (Profitability)
        if "OperatingMarginTTM" in profile:
            op_margin = api_wrapper.safe_float_or_empty(profile["OperatingMarginTTM"])
            if op_margin is not None:
                op_margin_value = op_margin * 100
                analysis["operating_margin"] = api_wrapper.format_financial_value(
                    op_margin_value, include_dollar=False, include_percent=True
                )

                # Enhanced operating margin evaluation based on industry patterns
                if op_margin_value > 25:
                    analysis["operating_margin_evaluation"] = (
                        "Elite operating efficiency - Exceptional cost control"
                    )
                elif op_margin_value > 15:
                    analysis["operating_margin_evaluation"] = (
                        "Excellent operating efficiency - Strong pricing power"
                    )
                elif op_margin_value > 10:
                    analysis["operating_margin_evaluation"] = (
                        "Good operating efficiency - Above average"
                    )
                elif op_margin_value > 5:
                    analysis["operating_margin_evaluation"] = (
                        "Average operating efficiency"
                    )
                else:
                    analysis["operating_margin_evaluation"] = (
                        "Below average operating efficiency - Potential cost structure issues"
                    )
            else:
                analysis["operating_margin"] = "No data"
                analysis["operating_margin_evaluation"] = (
                    "Unable to evaluate operating margin due to insufficient data"
                )

        # Net Profit Margin
        if "ProfitMargin" in profile:
            profit_margin = api_wrapper.safe_float_or_empty(profile["ProfitMargin"])
            if profit_margin is not None:
                profit_margin_value = profit_margin * 100
                analysis["profit_margin"] = api_wrapper.format_financial_value(
                    profit_margin_value, include_dollar=False, include_percent=True
                )

                # Enhanced profit margin evaluation
                if profit_margin_value > 20:
                    analysis["profit_margin_evaluation"] = (
                        "Elite profitability - Exceptional business model"
                    )
                elif profit_margin_value > 15:
                    analysis["profit_margin_evaluation"] = (
                        "Excellent profitability - Very strong business model"
                    )
                elif profit_margin_value > 10:
                    analysis["profit_margin_evaluation"] = (
                        "Strong profitability - Good business model"
                    )
                elif profit_margin_value > 5:
                    analysis["profit_margin_evaluation"] = "Average profitability"
                else:
                    analysis["profit_margin_evaluation"] = (
                        "Below average profitability - May indicate structural issues"
                    )
            else:
                analysis["profit_margin"] = "No data"
                analysis["profit_margin_evaluation"] = (
                    "Unable to evaluate profit margin due to insufficient data"
                )
    except Exception as e:
        analysis["profile_profitability_analysis_error"] = str(e)

    return analysis


def analyze_profitability_from_income_statement(
    api_wrapper, income_statement_data: Dict
) -> Dict:
    """Analyze profitability metrics from income statement data."""
    analysis = {}

    if not income_statement_data or "annualReports" not in income_statement_data:
        return analysis

    annual_reports = income_statement_data.get("annualReports", [])
    if len(annual_reports) < 2:
        return analysis

    try:
        recent = annual_reports[0]
        previous = annual_reports[1]

        # Extract key metrics
        recent_revenue = api_wrapper.safe_float_or_empty(recent.get("totalRevenue"))
        recent_gross_profit = api_wrapper.safe_float_or_empty(recent.get("grossProfit"))
        recent_operating_income = api_wrapper.safe_float_or_empty(
            recent.get("operatingIncome")
        )
        recent_net_income = api_wrapper.safe_float_or_empty(recent.get("netIncome"))
        ebitda = api_wrapper.safe_float_or_empty(recent.get("ebitda"))

        previous_revenue = api_wrapper.safe_float_or_empty(previous.get("totalRevenue"))
        previous_net_income = api_wrapper.safe_float_or_empty(previous.get("netIncome"))

        # Add basic metrics
        analysis["recent_revenue"] = api_wrapper.format_financial_value(recent_revenue)
        analysis["recent_gross_profit"] = api_wrapper.format_financial_value(
            recent_gross_profit
        )
        analysis["recent_operating_income"] = api_wrapper.format_financial_value(
            recent_operating_income
        )
        analysis["recent_net_income"] = api_wrapper.format_financial_value(
            recent_net_income
        )

        # Add EBITDA - important profitability metric
        if ebitda is not None:
            analysis["ebitda"] = api_wrapper.format_financial_value(ebitda)
            if recent_revenue is not None and recent_revenue > 0:
                ebitda_margin = (ebitda / recent_revenue) * 100
                analysis["ebitda_margin"] = f"{ebitda_margin:.2f}%"

                # EBITDA margin evaluation
                if ebitda_margin > 30:
                    analysis["ebitda_margin_evaluation"] = (
                        "Exceptional EBITDA margin - Elite operational efficiency"
                    )
                elif ebitda_margin > 20:
                    analysis["ebitda_margin_evaluation"] = (
                        "Excellent EBITDA margin - Strong operational efficiency"
                    )
                elif ebitda_margin > 15:
                    analysis["ebitda_margin_evaluation"] = (
                        "Good EBITDA margin - Above average operational efficiency"
                    )
                elif ebitda_margin > 10:
                    analysis["ebitda_margin_evaluation"] = "Average EBITDA margin"
                else:
                    analysis["ebitda_margin_evaluation"] = (
                        "Below average EBITDA margin - Operational efficiency concerns"
                    )

        # Calculate margin metrics if revenue data is available
        if recent_revenue is not None and recent_revenue > 0:
            # Gross Margin
            if recent_gross_profit is not None:
                gross_margin = (recent_gross_profit / recent_revenue) * 100
                analysis["gross_margin"] = f"{gross_margin:.2f}%"

                # Enhanced gross margin evaluation
                if gross_margin > 50:
                    analysis["gross_margin_evaluation"] = (
                        "Exceptional gross margins - Premium pricing power"
                    )
                elif gross_margin > 40:
                    analysis["gross_margin_evaluation"] = (
                        "Excellent gross margins - Strong pricing power"
                    )
                elif gross_margin > 30:
                    analysis["gross_margin_evaluation"] = (
                        "Good gross margins - Healthy pricing power"
                    )
                elif gross_margin > 20:
                    analysis["gross_margin_evaluation"] = "Average gross margins"
                else:
                    analysis["gross_margin_evaluation"] = (
                        "Below average gross margins - Limited pricing power"
                    )
            else:
                analysis["gross_margin"] = "No data"
                analysis["gross_margin_evaluation"] = (
                    "Unable to evaluate gross margins due to insufficient data"
                )

            # Operating Margin (if not already calculated from profile)
            if (
                recent_operating_income is not None
                and "operating_margin" not in analysis
            ):
                operating_margin = (recent_operating_income / recent_revenue) * 100
                analysis["operating_margin"] = f"{operating_margin:.2f}%"

                # Enhanced operating margin evaluation
                if operating_margin > 25:
                    analysis["operating_margin_evaluation"] = (
                        "Elite operating efficiency - Exceptional cost control"
                    )
                elif operating_margin > 15:
                    analysis["operating_margin_evaluation"] = (
                        "Excellent operating efficiency - Strong pricing power"
                    )
                elif operating_margin > 10:
                    analysis["operating_margin_evaluation"] = (
                        "Good operating efficiency - Above average"
                    )
                elif operating_margin > 5:
                    analysis["operating_margin_evaluation"] = (
                        "Average operating efficiency"
                    )
                else:
                    analysis["operating_margin_evaluation"] = (
                        "Below average operating efficiency - Potential cost structure issues"
                    )

            # Net Margin (if not already calculated from profile)
            if recent_net_income is not None and "net_margin" not in analysis:
                net_margin = (recent_net_income / recent_revenue) * 100
                analysis["net_margin"] = f"{net_margin:.2f}%"

                # Enhanced net margin evaluation
                if net_margin > 20:
                    analysis["net_margin_evaluation"] = (
                        "Elite net profitability - Exceptional business model"
                    )
                elif net_margin > 15:
                    analysis["net_margin_evaluation"] = (
                        "Excellent net profitability - Very strong business model"
                    )
                elif net_margin > 10:
                    analysis["net_margin_evaluation"] = (
                        "Strong net profitability - Good business model"
                    )
                elif net_margin > 5:
                    analysis["net_margin_evaluation"] = "Average net profitability"
                else:
                    analysis["net_margin_evaluation"] = (
                        "Below average net profitability - May indicate structural issues"
                    )

        # Growth metrics
        if (
            previous_revenue is not None
            and recent_revenue is not None
            and previous_revenue > 0
        ):
            revenue_growth = (
                (recent_revenue - previous_revenue) / previous_revenue
            ) * 100
            analysis["revenue_growth"] = f"{revenue_growth:.2f}%"

            if revenue_growth > 20:
                analysis["revenue_growth_evaluation"] = "Strong revenue growth"
            elif revenue_growth > 5:
                analysis["revenue_growth_evaluation"] = "Good revenue growth"
            elif revenue_growth > 0:
                analysis["revenue_growth_evaluation"] = "Modest revenue growth"
            else:
                analysis["revenue_growth_evaluation"] = "Declining revenue"
        else:
            analysis["revenue_growth"] = "No data"
            analysis["revenue_growth_evaluation"] = (
                "Unable to evaluate revenue growth due to insufficient data"
            )

        if (
            previous_net_income is not None
            and recent_net_income is not None
            and previous_net_income > 0
        ):
            net_income_growth = (
                (recent_net_income - previous_net_income) / previous_net_income
            ) * 100
            analysis["net_income_growth"] = f"{net_income_growth:.2f}%"

            # Net income growth evaluation
            if net_income_growth > 30:
                analysis["net_income_growth_evaluation"] = "Exceptional profit growth"
            elif net_income_growth > 20:
                analysis["net_income_growth_evaluation"] = "Strong profit growth"
            elif net_income_growth > 10:
                analysis["net_income_growth_evaluation"] = "Good profit growth"
            elif net_income_growth > 0:
                analysis["net_income_growth_evaluation"] = "Modest profit growth"
            else:
                analysis["net_income_growth_evaluation"] = (
                    "Declining profitability - Potential concerns"
                )
        else:
            analysis["net_income_growth"] = "No data"
            analysis["net_income_growth_evaluation"] = (
                "Unable to evaluate profit growth due to insufficient data"
            )

    except Exception as e:
        analysis["income_statement_profitability_analysis_error"] = str(e)

    return analysis


def calculate_overall_profitability_assessment(analysis: Dict) -> Dict:
    """Calculate the overall profitability assessment based on various factors."""
    try:
        profitability_factors = []

        # ROE assessment
        if "roe_evaluation" in analysis:
            if (
                "Exceptional" in analysis["roe_evaluation"]
                or "Excellent" in analysis["roe_evaluation"]
            ):
                profitability_factors.append(2)  # Strong positive
            elif "Good" in analysis["roe_evaluation"]:
                profitability_factors.append(1)  # Positive
            elif "Average" in analysis["roe_evaluation"]:
                profitability_factors.append(0)  # Neutral
            elif "Below" in analysis["roe_evaluation"]:
                profitability_factors.append(-1)  # Negative

        # Operating margin assessment
        if "operating_margin_evaluation" in analysis:
            if (
                "Elite" in analysis["operating_margin_evaluation"]
                or "Excellent" in analysis["operating_margin_evaluation"]
            ):
                profitability_factors.append(2)  # Strong positive
            elif "Good" in analysis["operating_margin_evaluation"]:
                profitability_factors.append(1)  # Positive
            elif "Average" in analysis["operating_margin_evaluation"]:
                profitability_factors.append(0)  # Neutral
            elif "Below" in analysis["operating_margin_evaluation"]:
                profitability_factors.append(-1)  # Negative

        # Net margin assessment
        if "net_margin_evaluation" in analysis:
            if (
                "Elite" in analysis["net_margin_evaluation"]
                or "Excellent" in analysis["net_margin_evaluation"]
            ):
                profitability_factors.append(2)  # Strong positive
            elif "Strong" in analysis["net_margin_evaluation"]:
                profitability_factors.append(1)  # Positive
            elif "Average" in analysis["net_margin_evaluation"]:
                profitability_factors.append(0)  # Neutral
            elif "Below" in analysis["net_margin_evaluation"]:
                profitability_factors.append(-1)  # Negative

        # ROA assessment if available
        if "roa_evaluation" in analysis:
            if (
                "Excellent" in analysis["roa_evaluation"]
                or "Strong" in analysis["roa_evaluation"]
            ):
                profitability_factors.append(2)  # Strong positive
            elif "Good" in analysis["roa_evaluation"]:
                profitability_factors.append(1)  # Positive
            elif "Average" in analysis["roa_evaluation"]:
                profitability_factors.append(0)  # Neutral
            elif "Inefficient" in analysis["roa_evaluation"]:
                profitability_factors.append(-1)  # Negative

        # Calculate overall profitability score if we have factors
        if profitability_factors:
            avg_score = sum(profitability_factors) / len(profitability_factors)

            # Provide overall profitability evaluation
            if avg_score > 1.5:
                analysis["overall_profitability_assessment"] = (
                    "Exceptional profitability - Industry leading performance"
                )
            elif avg_score > 0.75:
                analysis["overall_profitability_assessment"] = (
                    "Strong profitability - Above industry average performance"
                )
            elif avg_score > 0:
                analysis["overall_profitability_assessment"] = (
                    "Good profitability - Competitive performance"
                )
            elif avg_score > -0.5:
                analysis["overall_profitability_assessment"] = (
                    "Adequate profitability - Room for improvement"
                )
            else:
                analysis["overall_profitability_assessment"] = (
                    "Weak profitability - Significant concerns"
                )

        return analysis

    except Exception as e:
        analysis["overall_profitability_assessment_error"] = str(e)
        return analysis
