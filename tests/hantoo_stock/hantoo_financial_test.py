import sys
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
from src.graph.nodes.hantoo_financial import HantooFinancialAnalyzerNode
from langchain_core.messages import HumanMessage, AIMessage

# .env 파일 로드
load_dotenv()

# 경로 설정
sys.path.append("..")  # 상위 디렉토리 추가


class TestHantooFinancialNode(unittest.TestCase):
    """한투 재무제표 분석 노드 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        self.node = HantooFinancialAnalyzerNode()

    def test_extract_stock_code_from_result(self):
        """결과 텍스트에서 종목코드 추출 테스트"""
        testcases = [
            ("Financial Statement Analysis for Stock Code 005930", "005930"),
            ("Analysis shows that stock code 000660 has strong fundamentals", "000660"),
            ("The company with code 035420 shows improving metrics", "035420"),
            ("Financial analysis completed", "unknown"),  # 종목코드가 없는 경우
        ]

        for text, expected in testcases:
            result = self.node._extract_stock_code_from_result(text)
            self.assertEqual(result, expected, f"Text: {text}")

    @patch("src.graph.nodes.hantoo_financial.create_react_agent")
    def test_run(self, mock_create_agent):
        """노드 실행 테스트 - 전체 agent 모킹"""
        # 모킹할 결과 설정
        result_content = "Financial Statement Analysis for Stock Code 005930\n\nThe company shows strong financials..."

        # 모킹 에이전트 설정
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [AIMessage(content=result_content)]
        }
        mock_create_agent.return_value = mock_agent

        # 테스트 상태 객체
        state = {
            "llm": MagicMock(),
            "messages": [
                HumanMessage(content="Samsung Electronics financial analysis")
            ],  # 영어 메시지 사용
        }

        # 노드 실행
        self.node.agent = mock_agent  # 에이전트 직접 설정
        result = self.node._run(state)

        # 검증
        self.assertEqual(result.goto, "supervisor")
        self.assertEqual(result.update["financial_analysis"]["stock_code"], "005930")
        self.assertEqual(
            result.update["financial_analysis"]["analysis_text"], result_content
        )

    @patch("src.graph.nodes.hantoo_financial.create_react_agent")
    @patch("src.graph.nodes.hantoo_financial.ChatOpenAI")
    def test_invoke(self, mock_chat_openai, mock_create_agent):
        """API 엔드포인트 호출 테스트 - 에이전트 모킹"""
        # 결과 설정
        result_content = "Financial Statement Analysis for Stock Code 005930\n\nThe company shows strong financials..."

        # 모킹 에이전트 설정
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [AIMessage(content=result_content)]
        }
        mock_create_agent.return_value = mock_agent

        # _invoke 메소드 호출 (영어 메시지 사용)
        result = self.node._invoke("Samsung Electronics (005930) financial analysis")

        # 검증
        self.assertIsNotNone(result)
        self.assertIn("Financial Statement Analysis", result.answer)
        self.assertEqual(result.answer, result_content)


if __name__ == "__main__":
    unittest.main()
