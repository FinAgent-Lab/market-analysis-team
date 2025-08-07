import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import json

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.edgar_report.edgar_report import EdgarReporterWrapper


class TestEdgarReporterWrapper:
    """EdgarReporterWrapper 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """각 테스트 메서드 실행 전 실행"""
        # Mock SEC API client to avoid real API calls
        with patch('sec_edgar_api.EdgarClient'):
            self.wrapper = EdgarReporterWrapper()
            self.wrapper.edgar_client = Mock()
    
    def test_wrapper_initialization(self):
        """Wrapper 초기화 테스트"""
        assert self.wrapper is not None
        assert self.wrapper.user_agent == "Pseudo-lab/gomgomcode@gmail.com"
        print("✅ EdgarReporter 초기화 성공")
    
    def test_clean_company_name(self):
        """회사명 정리 기능 테스트"""
        test_cases = [
            ("Apple Inc", "apple"),
            ("Microsoft Corporation", "microsoft"),
            ("Tesla Inc.", "tesla"),
            ("Amazon.com Inc", "amazon.com"),
            ("Google LLC", "google"),
            ("Meta Platforms Inc", "meta platforms"),
            ("NVIDIA Corp", "nvidia"),
        ]
        
        for input_name, expected in test_cases:
            result = self.wrapper.clean_company_name(input_name)
            assert result == expected, f"Expected '{expected}' but got '{result}' for '{input_name}'"
        
        print("✅ 회사명 정리 기능 테스트 성공")
    
    @patch('requests.get')
    def test_find_company_cik_exact_match(self, mock_get):
        """CIK 정확한 일치 검색 테스트"""
        # Mock SEC company tickers response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "0": {
                "cik_str": 320193,
                "ticker": "AAPL",
                "title": "Apple Inc."
            },
            "1": {
                "cik_str": 1318605,
                "ticker": "TSLA", 
                "title": "Tesla Inc"
            }
        }
        mock_get.return_value = mock_response
        
        # Test exact ticker match
        result = self.wrapper.find_company_cik("AAPL")
        assert result is not None
        assert result['cik'] == "0000320193"
        assert result['ticker'] == "AAPL"
        assert result['company_name'] == "Apple Inc."
        
        # Test exact company name match
        result = self.wrapper.find_company_cik("Apple Inc.")
        assert result is not None
        assert result['cik'] == "0000320193"
        
        print("✅ CIK 정확한 일치 검색 테스트 성공")
    
    @patch('requests.get')
    def test_find_company_cik_cleaned_match(self, mock_get):
        """CIK 정리된 회사명 일치 검색 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "0": {
                "cik_str": 320193,
                "ticker": "AAPL",
                "title": "Apple Inc."
            }
        }
        mock_get.return_value = mock_response
        
        # Test cleaned name match
        result = self.wrapper.find_company_cik("Apple Corporation")
        assert result is not None
        assert result['cik'] == "0000320193"
        
        print("✅ CIK 정리된 회사명 일치 검색 테스트 성공")
    
    def test_get_company_filings_with_cik(self):
        """CIK로 회사 파일링 조회 테스트"""
        # Mock submissions response
        mock_submissions = {
            "cik": "0000320193",
            "name": "Apple Inc.",
            "tickers": ["AAPL"],
            "sicDescription": "ELECTRONIC COMPUTERS",
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q", "8-K"],
                    "filingDate": ["2023-10-27", "2023-08-03", "2023-05-04"],
                    "accessionNumber": ["0000320193-23-000106", "0000320193-23-000077", "0000320193-23-000064"]
                }
            }
        }
        
        self.wrapper.edgar_client.get_submissions.return_value = mock_submissions
        
        result = self.wrapper.get_company_filings("320193")
        
        assert result is not None
        assert result['cik'] == "0000320193"
        assert result['company_info']['name'] == "Apple Inc."
        assert len(result['recent_filings']['form']) == 3
        
        print("✅ CIK로 회사 파일링 조회 테스트 성공")
    
    @patch('requests.get')
    def test_get_company_filings_with_company_name(self, mock_get):
        """회사명으로 파일링 조회 테스트"""
        # Mock find_company_cik
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "0": {
                "cik_str": 320193,
                "ticker": "AAPL",
                "title": "Apple Inc."
            }
        }
        mock_get.return_value = mock_response
        
        # Mock submissions
        mock_submissions = {
            "cik": "0000320193",
            "name": "Apple Inc.",
            "filings": {
                "recent": {
                    "form": ["10-K"],
                    "filingDate": ["2023-10-27"],
                    "accessionNumber": ["0000320193-23-000106"]
                }
            }
        }
        
        self.wrapper.edgar_client.get_submissions.return_value = mock_submissions
        
        result = self.wrapper.get_company_filings("Apple")
        
        assert result is not None
        assert result['cik'] == "0000320193"
        
        print("✅ 회사명으로 파일링 조회 테스트 성공")
    
    @patch('src.tools.edgar_report.edgar_report.EdgarReporterWrapper.make_request')
    def test_get_10k_document_content(self, mock_make_request):
        """10-K 문서 내용 조회 테스트"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <body>
        <div>Item 1. Business</div>
        <p>Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.</p>
        <div>Item 1A. Risk Factors</div>
        <p>The Company's business can be impacted by political events, international trade disputes, war, terrorism, natural disasters, public health issues, and other business interruptions.</p>
        </body>
        </html>
        """
        mock_make_request.return_value = mock_response
        
        result = self.wrapper.get_10k_document_content("320193", "0000320193-23-000106")
        
        assert result is not None
        assert "Item 1. Business" in result
        assert "Apple Inc." in result
        
        print("✅ 10-K 문서 내용 조회 테스트 성공")
    
    def test_clean_html(self):
        """HTML 정리 기능 테스트"""
        html_content = """
        <html>
        <head><title>Test</title></head>
        <body>
        <script>alert('test');</script>
        <style>body { color: red; }</style>
        <div>Item 1. Business</div>
        <p>Apple Inc. designs and manufactures consumer electronics.</p>
        </body>
        </html>
        """
        
        cleaned_text = self.wrapper.clean_html(html_content)
        
        assert "alert('test');" not in cleaned_text
        assert "color: red;" not in cleaned_text
        assert "Item 1. Business" in cleaned_text
        assert "Apple Inc." in cleaned_text
        
        print("✅ HTML 정리 기능 테스트 성공")
    
    def test_extract_10k_items(self):
        """10-K 항목 추출 테스트"""
        mock_document = """
        <html>
        <body>
        <div>Table of Contents</div>
        <div>Item 1. Business</div>
        <div>Item 1A. Risk Factors</div>
        
        <h2>Item 1. Business</h2>
        <p>Apple Inc. (the "Company") designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories, and sells a range of related services. The Company's customers are primarily in the consumer, small and mid-sized business, education, enterprise and government markets. The Company sells its products worldwide through its retail stores, online stores, and direct sales force, as well as through third-party cellular network carriers, wholesalers, retailers, and resellers. In addition, the Company sells a range of third-party Apple compatible products, including application software and various accessories through its retail and online stores.</p>
        
        <h2>Item 1A. Risk Factors</h2>
        <p>The Company's business, reputation, results of operations, financial condition and stock price can be affected by a number of factors, whether currently known or unknown, including those described below. When any one or more of these risks materialize from time to time, the Company's business, reputation, results of operations, financial condition and stock price can be materially and adversely affected. The risks and uncertainties described below are not the only ones the Company faces. Additional risks and uncertainties not presently known to the Company or that the Company currently believes to be immaterial may also adversely affect the Company's business.</p>
        
        <h2>Item 7. Management's Discussion and Analysis</h2>
        <p>The following discussion should be read in conjunction with the consolidated financial statements and related notes included elsewhere in this report. This discussion contains forward-looking statements that involve risks and uncertainties. The Company's actual results could differ materially from those anticipated in these forward-looking statements as a result of various factors, including those discussed below and elsewhere in this report.</p>
        </body>
        </html>
        """
        
        extracted_items = self.wrapper.extract_10k_items(mock_document)
        
        assert "Item 1. Business" in extracted_items
        assert "Item 1A. Risk Factors" in extracted_items
        assert "Item 7. Management's Discussion and Analysis" in extracted_items
        
        # Check content extraction
        business_content = extracted_items["Item 1. Business"]
        assert "Apple Inc." in business_content
        assert "smartphones, personal computers" in business_content
        
        risk_content = extracted_items["Item 1A. Risk Factors"]
        assert "business, reputation, results of operations" in risk_content
        
        print("✅ 10-K 항목 추출 테스트 성공")
    
    @patch('src.tools.edgar_report.edgar_report.EdgarReporterWrapper.get_company_filings')
    @patch('src.tools.edgar_report.edgar_report.EdgarReporterWrapper.get_10k_document_content')
    def test_analyze_company_report_success(self, mock_get_document, mock_get_filings):
        """회사 보고서 분석 성공 테스트"""
        # Mock filing data
        mock_get_filings.return_value = {
            'company_info': {
                'name': 'Apple Inc.',
                'cik': '0000320193',
                'tickers': ['AAPL'],
                'sicDescription': 'ELECTRONIC COMPUTERS'
            },
            'recent_filings': {
                'form': ['10-K', '10-Q'],
                'filingDate': ['2023-10-27', '2023-08-03'],
                'accessionNumber': ['0000320193-23-000106', '0000320193-23-000077']
            },
            'cik': '0000320193'
        }
        
        # Mock document content
        mock_get_document.return_value = """
        <html><body>
        <h2>Item 1. Business</h2>
        <p>Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The Company's customers are primarily in the consumer, small and mid-sized business, education, enterprise and government markets.</p>
        </body></html>
        """
        
        result = self.wrapper.analyze_company_report("AAPL", "10-K")
        
        assert "📊 **SEC 10-K 보고서 분석** - Apple Inc." in result
        assert "### 🏢 회사 정보" in result
        assert "**회사명**: Apple Inc." in result
        assert "**CIK**: 0000320193" in result
        assert "**티커**: AAPL" in result
        assert "### 📄 최신 10-K 보고서 요약" in result
        assert "Item 1. Business" in result
        
        print("✅ 회사 보고서 분석 성공 테스트 통과")
    
    @patch('src.tools.edgar_report.edgar_report.EdgarReporterWrapper.get_company_filings')
    def test_analyze_company_report_company_not_found(self, mock_get_filings):
        """회사를 찾을 수 없는 경우 테스트"""
        mock_get_filings.return_value = None
        
        result = self.wrapper.analyze_company_report("UNKNOWN_COMPANY", "10-K")
        
        assert "❌ 'UNKNOWN_COMPANY'에 대한 회사 정보를 찾을 수 없습니다." in result
        
        print("✅ 회사를 찾을 수 없는 경우 테스트 통과")
    
    @patch('src.tools.edgar_report.edgar_report.EdgarReporterWrapper.get_company_filings')
    def test_analyze_company_report_no_filings(self, mock_get_filings):
        """해당 보고서 타입을 찾을 수 없는 경우 테스트"""
        mock_get_filings.return_value = {
            'company_info': {
                'name': 'Test Company',
                'cik': '0000123456'
            },
            'recent_filings': {
                'form': ['8-K'],  # 10-K나 10-Q가 없음
                'filingDate': ['2023-08-03'],
                'accessionNumber': ['0000123456-23-000001']
            },
            'cik': '0000123456'
        }
        
        result = self.wrapper.analyze_company_report("TEST", "10-K")
        
        assert "❌ 'Test Company'의 10-K 파일링을 찾을 수 없습니다." in result
        
        print("✅ 해당 보고서 타입을 찾을 수 없는 경우 테스트 통과")


if __name__ == "__main__":
    # Run tests directly
    import subprocess
    
    print("🚀 EDGAR Report 파싱 테스트 실행...")
    
    try:
        # Run specific test file
        result = subprocess.run([
            "python", "-m", "pytest", 
            "tests/test_edgar_report.py", 
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd="/home/hi/pseudo-co/market-analysis-team")
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        print(f"Return code: {result.returncode}")
        
    except Exception as e:
        print(f"테스트 실행 중 오류: {e}")