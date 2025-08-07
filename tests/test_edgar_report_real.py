"""
실제 SEC EDGAR API를 사용한 통합 테스트
네트워크 연결과 실제 데이터를 필요로 합니다.
"""
import pytest
import os
import sys
from unittest.mock import patch

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.edgar_report.edgar_report import EdgarReporterWrapper


class TestEdgarReporterRealAPI:
    """실제 SEC EDGAR API를 사용한 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """각 테스트 메서드 실행 전 실행"""
        # 실제 API 클라이언트 사용 (Mock 없이)
        self.wrapper = EdgarReporterWrapper()
    
    def test_real_apple_company_lookup(self):
        """실제 Apple 회사 정보 조회 테스트"""
        print("\n🔍 Apple 회사 정보 조회 테스트...")
        
        company_info = self.wrapper.find_company_cik("Apple")
        
        print(f"검색 결과: {company_info}")
        
        assert company_info is not None, "Apple 회사 정보를 찾을 수 없습니다"
        assert company_info['cik'] == "0000320193", f"예상 CIK: 0000320193, 실제: {company_info['cik']}"
        assert company_info['ticker'] == "AAPL", f"예상 티커: AAPL, 실제: {company_info['ticker']}"
        
        print("✅ Apple 회사 정보 조회 성공")
    
    @pytest.mark.skip(reason="네트워크 연결이 필요하고 시간이 오래 걸림")
    def test_real_apple_filings(self):
        """실제 Apple 파일링 조회 테스트"""
        print("\n📋 Apple 파일링 조회 테스트...")
        
        filing_data = self.wrapper.get_company_filings("AAPL")
        
        assert filing_data is not None, "Apple 파일링 데이터를 가져올 수 없습니다"
        
        company_info = filing_data['company_info']
        recent_filings = filing_data['recent_filings']
        
        print(f"회사명: {company_info.get('name')}")
        print(f"CIK: {company_info.get('cik')}")
        print(f"최근 파일링 수: {len(recent_filings.get('form', []))}")
        
        # 10-K 파일링이 있는지 확인
        has_10k = '10-K' in recent_filings.get('form', [])
        print(f"10-K 파일링 존재: {has_10k}")
        
        if has_10k:
            form_types = recent_filings['form']
            filing_dates = recent_filings['filingDate']
            accession_numbers = recent_filings['accessionNumber']
            
            for i, form in enumerate(form_types):
                if form == '10-K':
                    print(f"10-K 파일링: {filing_dates[i]} - {accession_numbers[i]}")
                    break
        
        assert has_10k, "Apple의 10-K 파일링을 찾을 수 없습니다"
        print("✅ Apple 파일링 조회 성공")
    
    @pytest.mark.skip(reason="네트워크 연결이 필요하고 시간이 오래 걸림")
    def test_real_document_download(self):
        """실제 SEC 문서 다운로드 테스트"""
        print("\n📄 실제 SEC 문서 다운로드 테스트...")
        
        # Apple의 최신 10-K 파일링 정보 가져오기
        filing_data = self.wrapper.get_company_filings("AAPL")
        assert filing_data is not None
        
        recent_filings = filing_data['recent_filings']
        cik = filing_data['cik']
        
        # 10-K 파일링 찾기
        form_types = recent_filings['form']
        accession_numbers = recent_filings['accessionNumber']
        
        latest_10k_accession = None
        for i, form in enumerate(form_types):
            if form == '10-K':
                latest_10k_accession = accession_numbers[i]
                break
        
        assert latest_10k_accession is not None, "10-K 파일링을 찾을 수 없습니다"
        
        print(f"다운로드할 문서: CIK={cik}, Accession={latest_10k_accession}")
        
        # 실제 문서 다운로드
        document_content = self.wrapper.get_10k_document_content(cik, latest_10k_accession)
        
        if document_content:
            print(f"문서 크기: {len(document_content)} characters")
            print(f"문서 시작 (첫 500자):\n{document_content[:500]}...")
            
            # HTML 태그가 있는지 확인
            has_html = '<html>' in document_content.lower() or '<body>' in document_content.lower()
            print(f"HTML 형식: {has_html}")
            
            # Item 1 Business가 포함되어 있는지 확인
            has_item1 = 'item 1' in document_content.lower() and 'business' in document_content.lower()
            print(f"Item 1 Business 포함: {has_item1}")
            
            assert document_content is not None, "문서 내용을 가져올 수 없습니다"
            assert len(document_content) > 1000, "문서 내용이 너무 짧습니다"
            
        else:
            print("❌ 문서 다운로드 실패")
            
            # 가능한 URL들 시도해보기
            accession_clean = latest_10k_accession.replace('-', '')
            base_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}"
            
            possible_urls = [
                f"{base_url}/{latest_10k_accession}.txt",
                f"{base_url}/form10k.htm",
                f"{base_url}/{latest_10k_accession}-10-k.htm",
                f"{base_url}/d{latest_10k_accession.split('-')[1]}.htm"
            ]
            
            print("시도된 URL들:")
            for url in possible_urls:
                print(f"  - {url}")
            
            assert False, "모든 URL에서 문서 다운로드 실패"
        
        print("✅ SEC 문서 다운로드 성공")
    
    def test_document_parsing_debug(self):
        """문서 파싱 디버깅 테스트"""
        print("\n🔍 문서 파싱 디버깅 테스트...")
        
        # 실제 10-K 문서의 일반적인 형식을 시뮬레이션
        sample_document = """
        <html>
        <head><title>Form 10-K</title></head>
        <body>
        <div>UNITED STATES SECURITIES AND EXCHANGE COMMISSION</div>
        <div>Washington, D.C. 20549</div>
        
        <h1>FORM 10-K</h1>
        
        <div>TABLE OF CONTENTS</div>
        <div>Item 1. Business .......................... 5</div>
        <div>Item 1A. Risk Factors .................... 15</div>
        <div>Item 7. Management's Discussion .......... 45</div>
        
        <div style="page-break-before: always;"></div>
        
        <h2>Item 1. Business</h2>
        <p>Apple Inc. (the "Company") designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories, and sells a range of related services. The Company's customers are primarily in the consumer, small and mid-sized business, education, enterprise and government markets. The Company sells its products worldwide through its retail stores, online stores, and direct sales force, as well as through third-party cellular network carriers, wholesalers, retailers, and resellers.</p>
        
        <h2>Item 1A. Risk Factors</h2>
        <p>The Company's business, reputation, results of operations, financial condition and stock price can be affected by a number of factors, whether currently known or unknown, including those described below. The risks described below are not the only ones the Company faces.</p>
        
        <h2>Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations</h2>
        <p>The following discussion should be read in conjunction with the consolidated financial statements and related notes included elsewhere in this report. This discussion contains forward-looking statements that involve risks and uncertainties.</p>
        
        <h2>Item 8. Financial Statements and Supplementary Data</h2>
        <p>See Note 1, "Summary of Significant Accounting Policies," of the Notes to Consolidated Financial Statements in Item 8 of this Form 10-K for additional information regarding the Company's revenue recognition policy.</p>
        
        </body>
        </html>
        """
        
        print("샘플 문서로 파싱 테스트...")
        
        # HTML 정리 테스트
        cleaned_text = self.wrapper.clean_html(sample_document)
        print(f"정리된 텍스트 길이: {len(cleaned_text)}")
        print(f"정리된 텍스트 샘플:\n{cleaned_text[:300]}...")
        
        # Item 추출 테스트
        extracted_items = self.wrapper.extract_10k_items(sample_document)
        
        print("\n추출된 항목들:")
        for item_name, content in extracted_items.items():
            print(f"\n{item_name}:")
            print(f"  내용 길이: {len(content)}")
            print(f"  내용 미리보기: {content[:100]}...")
            
            # 각 항목이 제대로 추출되었는지 확인
            if content == "해당 항목을 찾을 수 없습니다.":
                print(f"  ❌ {item_name} 추출 실패")
            else:
                print(f"  ✅ {item_name} 추출 성공")
        
        # 모든 항목이 추출되었는지 확인
        success_count = sum(1 for content in extracted_items.values() 
                          if content != "해당 항목을 찾을 수 없습니다.")
        total_count = len(extracted_items)
        
        print(f"\n추출 성공률: {success_count}/{total_count}")
        assert success_count >= 3, f"추출 성공률이 너무 낮습니다: {success_count}/{total_count}"
        
        print("✅ 문서 파싱 디버깅 테스트 완료")


def run_debug_test():
    """디버깅 테스트만 실행"""
    print("🔧 EDGAR 파싱 디버깅 테스트 실행...")
    
    # 직접 wrapper 생성
    from src.tools.edgar_report.edgar_report import EdgarReporterWrapper
    wrapper = EdgarReporterWrapper()
    
    try:
        print("\n🔍 Apple 회사 정보 조회 테스트...")
        company_info = wrapper.find_company_cik("Apple")
        print(f"검색 결과: {company_info}")
        
        if company_info:
            print("✅ Apple 회사 정보 조회 성공")
        else:
            print("❌ Apple 회사 정보 조회 실패")
        
        print("\n🔍 문서 파싱 디버깅 테스트...")
        
        # 실제 10-K 문서의 일반적인 형식을 시뮬레이션
        sample_document = """
        <html>
        <head><title>Form 10-K</title></head>
        <body>
        <div>UNITED STATES SECURITIES AND EXCHANGE COMMISSION</div>
        <div>Washington, D.C. 20549</div>
        
        <h1>FORM 10-K</h1>
        
        <div>TABLE OF CONTENTS</div>
        <div>Item 1. Business .......................... 5</div>
        <div>Item 1A. Risk Factors .................... 15</div>
        <div>Item 7. Management's Discussion .......... 45</div>
        
        <div style="page-break-before: always;"></div>
        
        <h2>Item 1. Business</h2>
        <p>Apple Inc. (the "Company") designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories, and sells a range of related services. The Company's customers are primarily in the consumer, small and mid-sized business, education, enterprise and government markets. The Company sells its products worldwide through its retail stores, online stores, and direct sales force, as well as through third-party cellular network carriers, wholesalers, retailers, and resellers.</p>
        
        <h2>Item 1A. Risk Factors</h2>
        <p>The Company's business, reputation, results of operations, financial condition and stock price can be affected by a number of factors, whether currently known or unknown, including those described below. The risks described below are not the only ones the Company faces.</p>
        
        <h2>Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations</h2>
        <p>The following discussion should be read in conjunction with the consolidated financial statements and related notes included elsewhere in this report. This discussion contains forward-looking statements that involve risks and uncertainties.</p>
        
        <h2>Item 8. Financial Statements and Supplementary Data</h2>
        <p>See Note 1, "Summary of Significant Accounting Policies," of the Notes to Consolidated Financial Statements in Item 8 of this Form 10-K for additional information regarding the Company's revenue recognition policy.</p>
        
        </body>
        </html>
        """
        
        print("샘플 문서로 파싱 테스트...")
        
        # HTML 정리 테스트
        cleaned_text = wrapper.clean_html(sample_document)
        print(f"정리된 텍스트 길이: {len(cleaned_text)}")
        print(f"정리된 텍스트 샘플:\n{cleaned_text[:300]}...")
        
        # Item 추출 테스트
        extracted_items = wrapper.extract_10k_items(sample_document)
        
        print("\n추출된 항목들:")
        for item_name, content in extracted_items.items():
            print(f"\n{item_name}:")
            print(f"  내용 길이: {len(content)}")
            print(f"  내용 미리보기: {content[:100]}...")
            
            # 각 항목이 제대로 추출되었는지 확인
            if content == "해당 항목을 찾을 수 없습니다.":
                print(f"  ❌ {item_name} 추출 실패")
            else:
                print(f"  ✅ {item_name} 추출 성공")
        
        # 모든 항목이 추출되었는지 확인
        success_count = sum(1 for content in extracted_items.values() 
                          if content != "해당 항목을 찾을 수 없습니다.")
        total_count = len(extracted_items)
        
        print(f"\n추출 성공률: {success_count}/{total_count}")
        
        print("\n✅ 모든 디버깅 테스트 완료")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_debug_test()