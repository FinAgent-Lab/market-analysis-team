import re
from typing import Dict, Optional


class FinancialScoringSystem:
    """Alpha Vantage 데이터 기반 재무 점수화 시스템"""

    def extract_number(self, text: str) -> Optional[float]:
        """텍스트에서 숫자 추출 (% 기호 및 기타 문자 제거)"""
        if not text or text == "No data" or text is None:
            return None

        # % 기호, 쉼표, 기타 문자 제거하고 숫자만 추출
        cleaned_text = (
            str(text).replace("%", "").replace(",", "").replace("$", "").strip()
        )

        # 음수와 소수점을 포함한 숫자 패턴 매칭
        match = re.search(r"(-?\d+\.?\d*)", cleaned_text)

        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def calculate_financial_scores(self, analysis: Dict) -> Dict:
        """전체 재무 점수 계산"""
        try:
            # 기존 분석에서 메트릭 추출
            roe = self.extract_number(analysis.get("roe", ""))
            roa = self.extract_number(analysis.get("roa", ""))
            operating_margin = self.extract_number(analysis.get("operating_margin", ""))
            current_ratio = self.extract_number(analysis.get("current_ratio", ""))
            debt_to_equity = self.extract_number(analysis.get("debt_to_equity", ""))

            # 개별 지표 점수 계산 (각각 0-100점)
            roe_score = self._score_roe(roe)
            roa_score = self._score_roa(roa)
            margin_score = self._score_operating_margin(operating_margin)
            liquidity_score = self._score_current_ratio(current_ratio)
            leverage_score = self._score_debt_to_equity(debt_to_equity)

            # 영역별 종합 점수 계산
            # 수익성: ROE(40%) + ROA(30%) + Operating Margin(30%)
            profitability_score = round(
                (roe_score * 0.4 + roa_score * 0.3 + margin_score * 0.3)
            )

            # 안정성: Current Ratio(60%) + Debt-to-Equity(40%)
            stability_score = round((liquidity_score * 0.6 + leverage_score * 0.4))

            # 전체 종합 점수: 수익성(60%) + 안정성(40%)
            overall_score = round((profitability_score * 0.6 + stability_score * 0.4))

            return {
                # 종합 점수
                "overall_score": overall_score,
                "overall_grade": self._get_grade(overall_score),
                # 영역별 점수
                "profitability_score": profitability_score,
                "profitability_grade": self._get_grade(profitability_score),
                "stability_score": stability_score,
                "stability_grade": self._get_grade(stability_score),
                # 개별 지표 점수
                "individual_scores": {
                    "roe_score": roe_score,
                    "roa_score": roa_score,
                    "operating_margin_score": margin_score,
                    "current_ratio_score": liquidity_score,
                    "debt_to_equity_score": leverage_score,
                },
                # 실제 메트릭 값들 (참고용)
                "metric_values": {
                    "roe": roe,
                    "roa": roa,
                    "operating_margin": operating_margin,
                    "current_ratio": current_ratio,
                    "debt_to_equity": debt_to_equity,
                },
                # 점수 해석
                "score_interpretation": self._get_score_interpretation(overall_score),
            }

        except Exception as e:
            # 점수 계산 실패 시 기본값 반환
            return {
                "overall_score": 0,
                "overall_grade": "N/A",
                "profitability_score": 0,
                "profitability_grade": "N/A",
                "stability_score": 0,
                "stability_grade": "N/A",
                "error": f"점수 계산 오류: {str(e)}",
                "individual_scores": {},
                "metric_values": {},
            }

    def _score_roe(self, roe: Optional[float]) -> int:
        """ROE 점수 계산 (0-100점)"""
        if roe is None:
            return 0

        if roe >= 20:
            return 100
        elif roe >= 15:
            return 85
        elif roe >= 10:
            return 70
        elif roe >= 7:
            return 55
        elif roe >= 5:
            return 40
        elif roe >= 0:
            return 25
        else:  # 음수 ROE
            return 10

    def _score_roa(self, roa: Optional[float]) -> int:
        """ROA 점수 계산 (0-100점)"""
        if roa is None:
            return 0

        if roa >= 12:
            return 100
        elif roa >= 8:
            return 85
        elif roa >= 5:
            return 70
        elif roa >= 3:
            return 55
        elif roa >= 1:
            return 40
        elif roa >= 0:
            return 25
        else:  # 음수 ROA
            return 10

    def _score_operating_margin(self, margin: Optional[float]) -> int:
        """영업이익률 점수 계산 (0-100점)"""
        if margin is None:
            return 0

        if margin >= 25:
            return 100
        elif margin >= 20:
            return 90
        elif margin >= 15:
            return 80
        elif margin >= 10:
            return 65
        elif margin >= 5:
            return 45
        elif margin >= 0:
            return 25
        else:  # 음수 영업이익률
            return 10

    def _score_current_ratio(self, ratio: Optional[float]) -> int:
        """유동비율 점수 계산 (0-100점)"""
        if ratio is None:
            return 0

        if ratio >= 3.0:
            return 100
        elif ratio >= 2.5:
            return 90
        elif ratio >= 2.0:
            return 80
        elif ratio >= 1.5:
            return 65
        elif ratio >= 1.2:
            return 45
        elif ratio >= 1.0:
            return 30
        else:  # 1.0 미만
            return 15

    def _score_debt_to_equity(self, ratio: Optional[float]) -> int:
        """부채비율 점수 계산 (0-100점) - 낮을수록 좋음"""
        if ratio is None:
            return 0

        if ratio <= 0.2:
            return 100
        elif ratio <= 0.4:
            return 90
        elif ratio <= 0.6:
            return 80
        elif ratio <= 0.8:
            return 65
        elif ratio <= 1.0:
            return 50
        elif ratio <= 1.5:
            return 35
        elif ratio <= 2.0:
            return 25
        else:  # 2.0 초과
            return 10

    def _get_grade(self, score: int) -> str:
        """점수를 등급으로 변환"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C+"
        elif score >= 40:
            return "C"
        else:
            return "D"

    def _get_score_interpretation(self, score: int) -> str:
        """점수 해석 텍스트 반환"""
        if score >= 90:
            return "최고 수준 - 매우 강력한 투자 후보"
        elif score >= 80:
            return "우수한 수준 - 강력한 투자 후보"
        elif score >= 70:
            return "양호한 수준 - 고려할만한 투자 대상"
        elif score >= 60:
            return "보통 수준 - 신중한 검토 필요"
        elif score >= 50:
            return "평균 이하 - 개선 사항 확인 필요"
        else:
            return "취약한 수준 - 주의 깊은 분석 필요"

    def format_score_summary(self, scores: Dict) -> str:
        """점수 요약 포맷팅"""
        if "error" in scores:
            return f"점수 계산 불가: {scores['error']}"

        summary = f"""
📊 **재무 건전성 종합 점수**

💯 **전체 평가**: {scores["overall_score"]}/100점 ({scores["overall_grade"]})
- 🔥 수익성: {scores["profitability_score"]}/100점 ({scores["profitability_grade"]})
- 🛡️ 안정성: {scores["stability_score"]}/100점 ({scores["stability_grade"]})

**투자 관점**: {scores["score_interpretation"]}
"""
        return summary


# 기존 analyze_financial_data 함수에 통합하는 코드
def add_scoring_to_analysis(analysis: Dict) -> Dict:
    """기존 분석 결과에 점수화 시스템 추가"""
    try:
        scoring_system = FinancialScoringSystem()
        financial_scores = scoring_system.calculate_financial_scores(analysis)
        analysis["financial_scores"] = financial_scores

        # 점수 요약도 추가
        analysis["score_summary"] = scoring_system.format_score_summary(
            financial_scores
        )

    except Exception as e:
        analysis["financial_scores"] = {
            "overall_score": 0,
            "overall_grade": "N/A",
            "error": f"점수 계산 실패: {str(e)}",
        }
        analysis["score_summary"] = "점수 계산을 완료할 수 없습니다."

    return analysis
