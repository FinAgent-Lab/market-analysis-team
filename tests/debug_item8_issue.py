#!/usr/bin/env python3
"""
MSFT Item 8 파싱 실패 문제 디버깅
"""
import sys
import os
import re

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.edgar_report.edgar_report import EdgarReporterWrapper


def debug_msft_item8():
    """MSFT Item 8 파싱 실패 원인 분석"""
    print("🔍 MSFT Item 8 파싱 실패 디버깅")
    print("=" * 50)
    
    wrapper = EdgarReporterWrapper()
    
    # MSFT 파일링 데이터 가져오기
    print("1. MSFT 파일링 데이터 조회...")
    filing_data = wrapper.get_company_filings("MSFT")
    
    if not filing_data:
        print("❌ 파일링 데이터를 가져올 수 없습니다.")
        return
        
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
    
    if not latest_10k:
        print("❌ 10-K 파일링을 찾을 수 없습니다.")
        return
        
    print(f"   최신 10-K: {latest_10k}")
    
    # 문서 다운로드
    print("\n2. SEC 문서 다운로드...")
    document_content = wrapper.get_10k_document_content(cik, latest_10k['accessionNumber'])
    
    if not document_content:
        print("❌ 문서 다운로드 실패")
        return
        
    print(f"   ✅ 문서 다운로드 성공: {len(document_content)} characters")
    
    # Item 8 패턴 상세 분석
    print("\n3. Item 8 패턴 상세 분석...")
    
    # 다양한 Item 8 패턴들
    item8_patterns = [
        r'Item\s+8\.?\s*Financial\s*Statements',
        r'ITEM\s+8\.?\s*FINANCIAL\s*STATEMENTS',
        r'Item\s+8\.?\s*Financial\s*Statements\s*and\s*Supplementary\s*Data',
        r'ITEM\s+8\.?\s*FINANCIAL\s*STATEMENTS\s*AND\s*SUPPLEMENTARY\s*DATA',
        r'8\.?\s*Financial\s*Statements',
        r'8\.?\s*FINANCIAL\s*STATEMENTS'
    ]
    
    all_matches = []
    for i, pattern in enumerate(item8_patterns):
        matches = list(re.finditer(pattern, document_content, re.IGNORECASE))
        print(f"   패턴 {i+1}: '{pattern}' → {len(matches)} 개 매치")
        
        for j, match in enumerate(matches):
            start_pos = match.start()
            end_pos = match.end()
            match_text = match.group()
            
            # 앞뒤 컨텍스트 추출
            context_start = max(0, start_pos - 100)
            context_end = min(len(document_content), end_pos + 500)
            context = document_content[context_start:context_end]
            
            # 줄바꿈과 공백 정리
            context_clean = re.sub(r'\s+', ' ', context).strip()
            
            match_info = {
                'pattern_idx': i,
                'match_idx': j,
                'start': start_pos,
                'end': end_pos,
                'text': match_text,
                'context': context_clean
            }
            all_matches.append(match_info)
            
            print(f"     매치 {j+1}: 위치 {start_pos}-{end_pos}")
            print(f"       텍스트: '{match_text}'")
            print(f"       컨텍스트: ...{context_clean[:200]}...")
    
    print(f"\n4. 전체 Item 8 매치 분석 (총 {len(all_matches)}개)")
    
    if not all_matches:
        print("❌ Item 8 패턴을 찾을 수 없습니다.")
        return
    
    # 각 매치에 대해 내용 추출 및 분석
    print("\n5. 각 매치에 대한 내용 추출 테스트...")
    
    for i, match_info in enumerate(all_matches):
        print(f"\n--- 매치 {i+1} 분석 ---")
        print(f"위치: {match_info['start']}-{match_info['end']}")
        print(f"매치 텍스트: '{match_info['text']}'")
        
        # 이 매치부터 다음 Item까지 내용 추출
        start_pos = match_info['end']
        
        # 다음 Item 패턴 찾기
        next_item_pattern = r'Item\s+\d+[A-Z]?\.?\s|\bItem\s+\d+[A-Z]?[\.\s]'
        remaining_text = document_content[start_pos:]
        next_match = re.search(next_item_pattern, remaining_text, re.IGNORECASE)
        
        if next_match:
            end_pos = start_pos + next_match.start()
            content = document_content[start_pos:end_pos].strip()
        else:
            # 다음 Item을 못 찾으면 최대 5000자까지
            content = document_content[start_pos:start_pos+5000].strip()
        
        # HTML 정리
        cleaned_content = wrapper.clean_html(f"<html><body>{content}</body></html>")
        word_count = len(cleaned_content.split())
        
        print(f"추출된 내용 길이: {len(content)} chars, {word_count} words")
        print(f"HTML 정리 후 길이: {len(cleaned_content)} chars")
        print(f"내용 미리보기: {cleaned_content[:300]}...")
        
        # 목차 판단 테스트
        is_toc = wrapper._is_table_of_contents(cleaned_content)
        print(f"목차 판단 결과: {is_toc}")
        
        # Financial Statements 특성 분석
        financial_keywords = [
            'income statement', 'balance sheet', 'cash flow', 'statement of operations',
            'consolidated', 'financial position', 'stockholders equity', 'revenue',
            'net income', 'assets', 'liabilities', 'in millions', 'fiscal year'
        ]
        
        keyword_count = sum(1 for keyword in financial_keywords 
                          if keyword.lower() in cleaned_content.lower())
        print(f"Financial keywords 발견: {keyword_count} 개")
        
        # 숫자 패턴 분석
        number_patterns = len(re.findall(r'\$[\d,]+|\d{1,3}(?:,\d{3})*', cleaned_content))
        print(f"숫자 패턴 발견: {number_patterns} 개")
        
        if word_count > 15 and not is_toc:
            print("✅ 이 매치는 유효한 Item 8 내용으로 판단됩니다!")
        else:
            print("❌ 이 매치는 제외됩니다.")


def test_item8_extraction_fix():
    """Item 8 추출 로직 개선 테스트"""
    print("\n🔧 Item 8 추출 로직 개선 테스트")
    print("=" * 50)
    
    wrapper = EdgarReporterWrapper()
    
    # 현재 로직으로 MSFT Item 8 추출 시도
    print("1. 현재 로직으로 MSFT 분석...")
    result = wrapper.analyze_company_report("MSFT", "10-K")
    
    # Item 8 부분만 추출
    item8_start = result.find("#### Item 8. Financial Statements and Supplementary Data")
    if item8_start != -1:
        item8_end = result.find("### 🔗 추가 정보", item8_start)
        if item8_end != -1:
            item8_section = result[item8_start:item8_end]
            print("현재 Item 8 결과:")
            print(item8_section)
            
            if "해당 항목을 찾을 수 없습니다" in item8_section:
                print("\n❌ 현재 로직으로는 Item 8을 추출할 수 없습니다.")
            else:
                print("\n✅ Item 8이 성공적으로 추출되었습니다.")
        else:
            print("Item 8 섹션의 끝을 찾을 수 없습니다.")
    else:
        print("Item 8 섹션을 찾을 수 없습니다.")


if __name__ == "__main__":
    try:
        debug_msft_item8()
        test_item8_extraction_fix()
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()