import sys
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
from src.graph.nodes.us_financial import USFinancialAnalyzerNode
from src.tools.us_stock.tool import USFinancialStatementTool
from langchain_core.messages import HumanMessage, AIMessage

# Load .env file
load_dotenv()

# Set path
sys.path.append("..")  # Add parent directory


class TestUSFinancialNode(unittest.TestCase):
    """Test class for US stock financial statement analysis node"""

    def setUp(self):
        """Test setup"""
        self.node = USFinancialAnalyzerNode()

    @patch("src.graph.nodes.us_financial.create_react_agent")
    @patch("src.tools.us_stock.tool.USFinancialStatementTool._extract_ticker")
    def test_run_with_explicit_ticker(self, mock_extract_ticker, mock_create_agent):
        """Test node execution with explicit ticker in query"""
        # Set up mocked ticker extraction
        mock_extract_ticker.return_value = "AAPL"

        # Set up mocked result
        result_content = "Financial Statement Analysis for Apple Inc (Ticker: AAPL)\n\nThe company shows strong financial health..."

        # Set up mocked agent
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [AIMessage(content=result_content)]
        }
        mock_create_agent.return_value = mock_agent

        # Test state object with English message containing a ticker
        state = {
            "llm": MagicMock(),
            "messages": [HumanMessage(content="Analyze AAPL financials")],
        }

        # Execute node
        self.node.agent = mock_agent
        result = self.node._run(state)

        # Verify
        self.assertEqual(result.goto, "supervisor")
        self.assertEqual(
            result.update["financial_analysis"]["ticker"], "AAPL"
        )  # LLM 추출 결과 사용
        self.assertEqual(result.update["financial_analysis"]["market"], "US")
        self.assertEqual(
            result.update["financial_analysis"]["analysis_text"], result_content
        )

    @patch("src.graph.nodes.us_financial.create_react_agent")
    @patch("src.tools.us_stock.tool.USFinancialStatementTool._extract_ticker")
    def test_run_with_company_name(self, mock_extract_ticker, mock_create_agent):
        """Test node execution with company name instead of ticker"""
        # Set up mocked ticker extraction (simulating LLM-based inference)
        mock_extract_ticker.return_value = "AAPL"

        # Set up mocked result
        result_content = "Financial Statement Analysis for Apple Inc (Ticker: AAPL)\n\nThe company shows strong financial health..."

        # Set up mocked agent
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [AIMessage(content=result_content)]
        }
        mock_create_agent.return_value = mock_agent

        # Test state object with English message containing only company name
        state = {
            "llm": MagicMock(),
            "messages": [HumanMessage(content="Analyze Apple's financial status")],
        }

        # Execute node
        self.node.agent = mock_agent
        result = self.node._run(state)

        # Verify
        self.assertEqual(result.goto, "supervisor")
        self.assertEqual(
            result.update["financial_analysis"]["ticker"], "AAPL"
        )  # LLM 추출 결과 사용
        self.assertEqual(result.update["financial_analysis"]["market"], "US")
        self.assertEqual(
            result.update["financial_analysis"]["analysis_text"], result_content
        )

    @patch("src.graph.nodes.us_financial.create_react_agent")
    @patch("src.tools.us_stock.tool.USFinancialStatementTool._extract_ticker")
    def test_llm_ticker_extraction(self, mock_extract_ticker, mock_create_agent):
        """Test the LLM-based ticker extraction flow"""
        # Set LLM extraction to return MSFT
        mock_extract_ticker.return_value = "MSFT"  # Simulating LLM inference

        # Set up mocked result
        result_content = "Financial Statement Analysis for Microsoft Corporation (Ticker: MSFT)\n\nThe company shows strong financial health..."

        # Set up mocked agent
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [AIMessage(content=result_content)]
        }
        mock_create_agent.return_value = mock_agent

        # Test state object with ambiguous query
        state = {
            "llm": MagicMock(),
            "messages": [
                HumanMessage(content="Analyze Microsoft's financial performance")
            ],
        }

        # Execute node
        self.node.agent = mock_agent
        result = self.node._run(state)

        # Verify
        self.assertEqual(result.goto, "supervisor")
        self.assertEqual(
            result.update["financial_analysis"]["ticker"], "MSFT"
        )  # LLM 추출 결과 사용
        self.assertEqual(result.update["financial_analysis"]["market"], "US")

    @patch("src.graph.nodes.us_financial.create_react_agent")
    @patch("src.tools.us_stock.tool.USFinancialStatementTool._extract_ticker")
    def test_no_company_identified(self, mock_extract_ticker, mock_create_agent):
        """Test when neither ticker nor company can be identified"""
        # Set up extraction to return None (no ticker identified)
        mock_extract_ticker.return_value = None

        # Set up mocked result
        result_content = "I need more information. Please provide a specific company name or ticker symbol for financial analysis."

        # Set up mocked agent
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [AIMessage(content=result_content)]
        }
        mock_create_agent.return_value = mock_agent

        # Test state object with vague query
        state = {
            "llm": MagicMock(),
            "messages": [HumanMessage(content="Analyze a technology company")],
        }

        # Execute node
        self.node.agent = mock_agent
        result = self.node._run(state)

        # Verify - LLM 추출 실패 시 "unknown" 반환
        self.assertEqual(result.goto, "supervisor")
        self.assertEqual(result.update["financial_analysis"]["ticker"], "unknown")
        self.assertEqual(result.update["financial_analysis"]["market"], "US")

    @patch("src.graph.nodes.us_financial.create_react_agent")
    def test_non_english_query(self, mock_create_agent):
        """Test handling of non-English queries"""
        # Set up mocked result with English response, even though query is non-English
        result_content = "Financial Statement Analysis for Apple Inc (Ticker: AAPL)\n\nThe company shows strong financial health..."

        # Set up mocked agent
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [AIMessage(content=result_content)]
        }
        mock_create_agent.return_value = mock_agent

        # Test state object with non-English message
        state = {
            "llm": MagicMock(),
            "messages": [HumanMessage(content="애플 회사의 재무 상태를 분석해 주세요")],
        }

        # We need to mock the tool's _extract_ticker to handle Korean text
        with patch.object(
            USFinancialStatementTool, "_extract_ticker", return_value="AAPL"
        ):
            # Execute node
            self.node.agent = mock_agent
            result = self.node._run(state)

            # Verify
            self.assertEqual(result.goto, "supervisor")
            self.assertEqual(
                result.update["financial_analysis"]["ticker"], "AAPL"
            )  # LLM 추출 결과 사용
            self.assertEqual(result.update["financial_analysis"]["market"], "US")


if __name__ == "__main__":
    unittest.main()
