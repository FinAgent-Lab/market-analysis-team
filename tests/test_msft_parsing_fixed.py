#!/usr/bin/env python3
"""
MSFT 실제 SEC 문서 파싱 테스트
"""
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.edgar_report.edgar_report import EdgarReporterWrapper


def test_msft_real_parsing():
    """MSFT 실제 파싱 테스트"""
    print("🔍 MSFT 실제 SEC 문서 파싱 테스트")
    print("=" * 50)
    
    wrapper = EdgarReporterWrapper()
    
    # MSFT 분석 실행
    print("1. MSFT 10-K 보고서 분석 실행...")
    result = wrapper.analyze_company_report("MSFT", "10-K")
    
    print("2. 분석 결과:")
    print("-" * 40)
    print(result)
    print("-" * 40)
    
    # 각 Item의 추출 상태 확인
    print("\n3. Item별 추출 상태 분석:")
    items_to_check = [
        "Item 1. Business",
        "Item 1A. Risk Factors", 
        "Item 7. Management's Discussion and Analysis",
        "Item 8. Financial Statements and Supplementary Data"
    ]
    
    for item_name in items_to_check:
        if item_name in result:
            # 해당 항목 뒤의 내용 추출
            start_idx = result.find(item_name)
            if start_idx != -1:
                # ```로 감싸진 내용 찾기
                content_start = result.find("```", start_idx)
                if content_start != -1:
                    content_end = result.find("```", content_start + 3)
                    if content_end != -1:
                        content = result[content_start + 3:content_end].strip()
                        
                        if content == "해당 항목을 찾을 수 없습니다.":
                            print(f"   ❌ {item_name}: 추출 실패")
                        else:
                            print(f"   ✅ {item_name}: 추출 성공 ({len(content)} chars)")
                            print(f"      미리보기: {content[:100]}...")
    
    # 개별 문서 조회 테스트
    print("\n4. 개별 문서 조회 디버깅...")
    filing_data = wrapper.get_company_filings("MSFT")
    
    if filing_data:
        recent_filings = filing_data['recent_filings']
        cik = filing_data['cik']
        
        # 최신 10-K 찾기
        latest_10k = None
        for i, form in enumerate(recent_filings['form']):
            if form == '10-K':
                latest_10k = {
                    'accessionNumber': recent_filings['accessionNumber'][i],
                    'filingDate': recent_filings['filingDate'][i]
                }
                break
        
        if latest_10k:
            print(f"   최신 10-K: {latest_10k}")
            
            # 문서 다운로드 시도
            document_content = wrapper.get_10k_document_content(cik, latest_10k['accessionNumber'])
            
            if document_content:
                print(f"   ✅ 문서 다운로드 성공: {len(document_content)} characters")
                
                # 간단한 Item 검색
                import re
                item_patterns = [
                    (r'Item\s+1\.?\s*Business', 'Item 1. Business'),
                    (r'Item\s+1A\.?\s*Risk', 'Item 1A. Risk Factors'),
                    (r'Item\s+7\.?\s*Management', 'Item 7. Management'),
                    (r'Item\s+8\.?\s*Financial', 'Item 8. Financial')
                ]
                
                for pattern, name in item_patterns:
                    matches = list(re.finditer(pattern, document_content, re.IGNORECASE))
                    print(f"   패턴 '{name}': {len(matches)} 개 발견")
                    
                    if matches:
                        # 첫 번째 매치의 앞뒤 컨텍스트 출력
                        match = matches[0]
                        start = max(0, match.start() - 50)
                        end = min(len(document_content), match.end() + 200)
                        context = document_content[start:end].replace('\n', ' ')
                        print(f"      컨텍스트: ...{context}...")
            else:
                print("   ❌ 문서 다운로드 실패")
        else:
            print("   ❌ 10-K 파일링을 찾을 수 없음")
    else:
        print("   ❌ 파일링 데이터를 가져올 수 없음")


if __name__ == "__main__":
    try:
        test_msft_real_parsing()
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()