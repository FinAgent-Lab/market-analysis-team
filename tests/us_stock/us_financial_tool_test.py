import sys
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
from src.tools.us_stock.tool import USFinancialStatementTool
from src.graph.nodes.us_financial import USFinancialAnalyzerNode

# Load .env file
load_dotenv()

# Set path
sys.path.append("..")  # Add parent directory


class TestTickerExtraction(unittest.TestCase):
    """Test class for ticker symbol extraction functionality"""

    def setUp(self):
        """Test setup"""
        self.tool = USFinancialStatementTool()

        # Set up mock LLM for all tests
        mock_llm = MagicMock()

        # Configure mock LLM to return appropriate responses for different queries
        def mock_predict(prompt):
            # Extract the query from the prompt
            if "Identify the US stock market ticker symbol" in prompt:
                try:
                    # Extract query from double quotes
                    parts = prompt.split('"')
                    if len(parts) >= 3:
                        query = parts[1]
                    else:
                        query = ""

                    # Map common test queries to expected ticker symbols
                    query_to_ticker = {
                        "Analyze financials for AAPL": "AAPL",
                        "What's the financial status of ticker MSFT?": "MSFT",
                        "Do a financial analysis of TSLA": "TSLA",
                        "Ticker: AMZN financial analysis": "AMZN",
                        "Google GOOG financial statements": "GOOG",
                        "Apple (AAPL) financial status": "AAPL",
                        "Analyze Apple's financials": "AAPL",
                        "How is Microsoft doing?": "MSFT",
                        "Google's financial status": "GOOGL",
                        "Should I invest in Tesla?": "TSLA",
                        "Amazon financial analysis": "AMZN",
                        "Facebook (Meta) performance?": "META",
                        "How is Nvidia's financial health?": "NVDA",
                        "Netflix stock analysis": "NFLX",
                    }

                    # Check for exact match first
                    if query in query_to_ticker:
                        return query_to_ticker[query]

                    # Check for keyword matches if no exact match
                    for keyword, ticker in [
                        ("Apple", "AAPL"),
                        ("Microsoft", "MSFT"),
                        ("Google", "GOOGL"),
                        ("Tesla", "TSLA"),
                        ("Amazon", "AMZN"),
                        ("Meta", "META"),
                        ("Facebook", "META"),
                        ("Nvidia", "NVDA"),
                        ("Netflix", "NFLX"),
                    ]:
                        if keyword.lower() in query.lower():
                            return ticker

                    # Return default for unknown companies or empty queries
                    return "UNKNOWN"
                except Exception:
                    return "UNKNOWN"

            # Default response for other prompts
            return "Default mock response"

        mock_llm.predict = mock_predict
        self.tool.llm = mock_llm
        self.node = USFinancialAnalyzerNode()

    def tearDown(self):
        """Clean up after tests"""
        # Any cleanup code if needed
        pass

    def test_explicit_ticker_extraction(self):
        """Test extraction of explicitly mentioned tickers"""
        testcases = [
            ("Analyze financials for AAPL", "AAPL"),
            ("What's the financial status of ticker MSFT?", "MSFT"),
            ("Do a financial analysis of TSLA", "TSLA"),
            ("Ticker: AMZN financial analysis", "AMZN"),
            ("Google GOOG financial statements", "GOOG"),
            ("Apple (AAPL) financial status", "AAPL"),
        ]

        for query, expected in testcases:
            result = self.tool._extract_ticker(query)
            self.assertEqual(result, expected, f"Query: {query}")

    def test_company_name_to_ticker_mapping(self):
        """Test extraction of tickers from company names using mapping dictionary"""
        testcases = [
            ("Analyze Apple's financials", "AAPL"),
            ("How is Microsoft doing?", "MSFT"),
            ("Google's financial status", "GOOGL"),
            ("Should I invest in Tesla?", "TSLA"),
            ("Amazon financial analysis", "AMZN"),
            ("Facebook (Meta) performance?", "META"),
        ]

        for query, expected in testcases:
            result = self.tool._extract_ticker(query)
            self.assertEqual(result, expected, f"Query: {query}")

    def test_no_ticker_extraction(self):
        """Test cases where no ticker can be extracted"""
        # For these queries, set up the LLM to return "UNKNOWN"
        testcases = [
            "Analyze financial statements",
            "How's the stock market?",
            "Recent corporate earnings trends",
            "Recommend good investments",
        ]

        for query in testcases:
            # Mock the LLM to return "UNKNOWN" for these specific queries
            with patch.object(self.tool.llm, "predict", return_value="UNKNOWN"):
                result = self.tool._extract_ticker(query)
                self.assertIsNone(result, f"Query: {query}")

    @patch(
        "src.tools.us_stock.alpha_vantage.AlphaVantageAPIWrapper.get_company_overview"
    )
    def test_llm_ticker_extraction(self, mock_get_company_overview):
        """Test ticker extraction using LLM"""
        # Alpha Vantage API 모킹 - 성공 케이스
        mock_get_company_overview.return_value = {
            "Symbol": "NVDA",
            "Name": "NVIDIA Corporation",
        }

        # 테스트 시나리오
        result = self.tool._extract_ticker("How is Nvidia's financial health?")
        self.assertEqual(result, "NVDA", "Should extract NVDA for Nvidia")

        # API 오류 케이스 모킹
        mock_get_company_overview.return_value = {"error": "Invalid API call"}
        result = self.tool._extract_ticker("Analyze an unknown company")
        self.assertIsNone(result, "Should return None for invalid ticker")

    @patch("src.graph.nodes.us_financial.create_react_agent")
    @patch("src.tools.us_stock.tool.USFinancialStatementTool._extract_ticker")
    def test_node_with_various_queries(self, mock_extract_ticker, mock_create_agent):
        """Test node behavior with various query types"""
        # Setup test cases
        test_cases = [
            {
                "query": "Analyze AAPL financials",
                "extracted_ticker": "AAPL",
                "success": True,
            },
            {
                "query": "What's Apple's financial status?",
                "extracted_ticker": "AAPL",  # Extracted from mapping dictionary
                "success": True,
            },
            {
                "query": "Analyze an AI company",
                "extracted_ticker": "NVDA",  # Inferred by LLM
                "success": True,
            },
            {
                "query": "Analyze the stock market",
                "extracted_ticker": None,  # Extraction failed
                "success": False,
            },
        ]

        for case in test_cases:
            # Mock ticker extraction
            mock_extract_ticker.return_value = case["extracted_ticker"]

            # Mock agent response
            mock_agent = MagicMock()
            if case["success"]:
                # 분석 결과가 포함된 응답 (티커는 이제 중요하지 않음, LLM에서 추출한 것 사용)
                result_content = (
                    "Financial Statement Analysis for Company\n\nThe company shows..."
                )
            else:
                result_content = "I need more information. Please provide a specific ticker symbol for analysis."

            mock_agent.invoke.return_value = {
                "messages": [MagicMock(content=result_content)]
            }
            mock_create_agent.return_value = mock_agent

            # State object for node execution
            state = {"llm": MagicMock(), "messages": [MagicMock(content=case["query"])]}

            # Execute node
            self.node.agent = mock_agent
            result = self.node._run(state)

            # Verify results
            if case["success"]:
                # LLM이 추출한 티커를 직접 사용하므로, 이제 success 케이스에선 extracted_ticker와 같아야 함
                self.assertEqual(
                    result.update["financial_analysis"]["ticker"],
                    case["extracted_ticker"],
                )
            else:
                # 추출 실패 시 "unknown" 대신 None 반환
                self.assertEqual(
                    result.update["financial_analysis"]["ticker"], "unknown"
                )


if __name__ == "__main__":
    unittest.main()