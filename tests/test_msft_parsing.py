#!/usr/bin/env python3
"""
MSFT 실제 SEC 문서 파싱 테스트
"""
import sys
import os
import requests
from bs4 import BeautifulSoup
import re

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.edgar_report.edgar_report import EdgarReporterWrapper


def test_msft_real_document():
    """MSFT 실제 SEC 문서 다운로드 및 분석"""
    print("🔍 MSFT 실제 SEC 문서 분석 테스트")
    print("=" * 60)
    
    wrapper = EdgarReporterWrapper()
    
    # MSFT 정보 조회
    print("1. MSFT 회사 정보 조회...")
    company_info = wrapper.find_company_cik("MSFT")
    print(f"   회사 정보: {company_info}")
    
    if not company_info:
        print("❌ MSFT 회사 정보를 찾을 수 없습니다.")
        return
    
    # 파일링 정보 조회
    print("\n2. MSFT 파일링 정보 조회...")
    filing_data = wrapper.get_company_filings("MSFT")
    
    if not filing_data:
        print("❌ MSFT 파일링 정보를 찾을 수 없습니다.")
        return
        
    recent_filings = filing_data['recent_filings']
    cik = filing_data['cik']
    
    # 최신 10-K 찾기
    print("3. 최신 10-K 파일링 찾기...")
    latest_10k = None
    form_types = recent_filings['form']
    filing_dates = recent_filings['filingDate']
    accession_numbers = recent_filings['accessionNumber']
    
    for i, form in enumerate(form_types):
        if form == '10-K':
            latest_10k = {
                'form': form,
                'filingDate': filing_dates[i],
                'accessionNumber': accession_numbers[i]
            }
            break
    
    if not latest_10k:
        print("❌ 10-K 파일링을 찾을 수 없습니다.")
        return
        
    print(f"   최신 10-K: {latest_10k}")
    
    # 실제 문서 다운로드 시도
    print("\n4. 실제 SEC 문서 다운로드 시도...")
    accession_number = latest_10k['accessionNumber']
    document_content = wrapper.get_10k_document_content(cik, accession_number)
    
    if document_content:
        print(f"   ✅ 문서 다운로드 성공: {len(document_content)} characters")
        
        # 문서 형식 분석
        print("\n5. 문서 형식 분석...")
        is_html = '<html>' in document_content.lower() or '<body>' in document_content.lower()
        is_xml = '<?xml' in document_content[:100].lower()
        has_xbrl = 'xbrl' in document_content.lower()
        
        print(f"   HTML 형식: {is_html}")
        print(f"   XML 형식: {is_xml}")
        print(f"   XBRL 포함: {has_xbrl}")
        
        # 문서 시작 부분 출력
        print(f"\n6. 문서 시작 부분 (첫 1000자):")
        print("-" * 40)
        print(document_content[:1000])
        print("-" * 40)
        
        # Item 패턴 검색
        print("\n7. Item 패턴 검색...")
        item_patterns = [
            r'Item\s+1\.\s*Business',
            r'Item\s+1A\.\s*Risk\s*Factors', 
            r'Item\s+7\.\s*Management',
            r'Item\s+8\.\s*Financial'
        ]
        
        for pattern in item_patterns:
            matches = list(re.finditer(pattern, document_content, re.IGNORECASE))
            print(f"   패턴 '{pattern}': {len(matches)} 개 매치")
            
            for i, match in enumerate(matches[:3]):  # 최대 3개만 출력
                start = max(0, match.start() - 50)
                end = min(len(document_content), match.end() + 100)
                context = document_content[start:end].replace('\n', ' ')
                print(f"     매치 {i+1}: ...{context}...")
        
        # 파싱 테스트
        print("\n8. 현재 파싱 로직으로 추출 테스트...")
        extracted_items = wrapper.extract_10k_items(document_content)
        
        for item_name, content in extracted_items.items():
            success = content != "해당 항목을 찾을 수 없습니다."
            status = "✅" if success else "❌"
            print(f"   {status} {item_name}: {len(content)} chars")
            if success:
                print(f"      미리보기: {content[:150]}...")
        
    else:
        print("❌ 문서 다운로드 실패")
        
        # 가능한 URL들 시도
        print("\n5. 가능한 문서 URL들 직접 테스트...")
        test_direct_urls(cik, accession_number)


def test_direct_urls(cik, accession_number):
    """가능한 URL들을 직접 테스트"""
    user_agent = "Pseudo-lab/gomgomcode@gmail.com"
    headers = {'User-Agent': user_agent}
    
    accession_clean = accession_number.replace('-', '')
    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}"
    
    # 다양한 파일명 패턴들
    possible_filenames = [
        f"{accession_number}.txt",
        "form10k.htm",
        f"{accession_number}-10-k.htm",
        f"d{accession_number.split('-')[1]}.htm",
        f"msft-{accession_number.split('-')[1]}.htm",
        "10k.htm",
        "form10k.html",
        "index.html"
    ]
    
    print(f"Base URL: {base_url}")
    
    for filename in possible_filenames:
        url = f"{base_url}/{filename}"
        print(f"\n시도 중: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', 'unknown')
                print(f"  Content-Type: {content_type}")
                print(f"  내용 길이: {len(response.text)} characters")
                
                # 내용 미리보기
                preview = response.text[:300].replace('\n', ' ')
                print(f"  내용 미리보기: {preview}...")
                
                # Item 검색
                item_count = len(re.findall(r'Item\s+\d+[A-Z]?\.', response.text, re.IGNORECASE))
                print(f"  Item 패턴 발견: {item_count} 개")
                
                if item_count > 0:
                    print("  ✅ 이 URL에서 Item들을 발견했습니다!")
                    return response.text
                    
        except Exception as e:
            print(f"  오류: {e}")
    
    print("\n❌ 모든 URL에서 문서를 가져올 수 없습니다.")
    return None


def analyze_sec_filing_structure():
    """SEC 파일링 구조 분석"""
    print("\n🔍 SEC 파일링 구조 분석")
    print("=" * 40)
    
    # 실제 SEC 문서에서 나타나는 다양한 Item 형식들
    real_item_formats = [
        # 일반적인 형식
        "Item 1. Business",
        "Item 1A. Risk Factors", 
        "Item 7. Management's Discussion and Analysis",
        "Item 8. Financial Statements and Supplementary Data",
        
        # 대문자
        "ITEM 1. BUSINESS",
        "ITEM 1A. RISK FACTORS",
        
        # 탭 구분
        "Item 1.\tBusiness",
        "Item 1A.\tRisk Factors",
        
        # 공백 없음
        "Item 1.Business",
        "Item 1A.Risk Factors",
        
        # 긴 제목
        "Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations",
        "Item 7.\tManagement's Discussion and Analysis of Financial Condition and Results of Operations",
        
        # HTML 태그 포함
        "<b>Item 1. Business</b>",
        "<h2>Item 1A. Risk Factors</h2>",
        "<div>Item 7. Management's Discussion and Analysis</div>",
        
        # 번호만
        "1. Business",
        "1A. Risk Factors",
        "7. Management's Discussion and Analysis",
    ]
    
    # 개선된 정규식 패턴들
    improved_patterns = {
        "Item 1": [
            r'(?:Item\s+)?1\.?\s*Business',
            r'<[^>]*>(?:Item\s+)?1\.?\s*Business</[^>]*>',
            r'(?:ITEM\s+)?1\.?\s*BUSINESS',
        ],
        "Item 1A": [
            r'(?:Item\s+)?1A\.?\s*Risk\s*Factors',
            r'<[^>]*>(?:Item\s+)?1A\.?\s*Risk\s*Factors</[^>]*>',
            r'(?:ITEM\s+)?1A\.?\s*RISK\s*FACTORS',
        ],
        "Item 7": [
            r'(?:Item\s+)?7\.?\s*Management[\'']?s?\s*Discussion',
            r'<[^>]*>(?:Item\s+)?7\.?\s*Management[\'']?s?\s*Discussion</[^>]*>',
            r'(?:ITEM\s+)?7\.?\s*MANAGEMENT[\'']?S?\s*DISCUSSION',
        ],
        "Item 8": [
            r'(?:Item\s+)?8\.?\s*Financial\s*Statements',
            r'<[^>]*>(?:Item\s+)?8\.?\s*Financial\s*Statements</[^>]*>',
            r'(?:ITEM\s+)?8\.?\s*FINANCIAL\s*STATEMENTS',
        ]
    }
    
    print("실제 SEC 문서에서 발견되는 Item 형식들:")
    for format_text in real_item_formats:
        print(f"  '{format_text}'")
    
    print("\n개선된 정규식 패턴 테스트:")
    for item_name, patterns in improved_patterns.items():
        print(f"\n{item_name}:")
        for pattern in patterns:
            print(f"  패턴: {pattern}")
            
            match_count = 0
            for format_text in real_item_formats:
                if re.search(pattern, format_text, re.IGNORECASE):
                    match_count += 1
            
            coverage = (match_count / len(real_item_formats)) * 100
            print(f"  매치율: {match_count}/{len(real_item_formats)} ({coverage:.1f}%)")


if __name__ == "__main__":
    try:
        test_msft_real_document()
        analyze_sec_filing_structure()
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()