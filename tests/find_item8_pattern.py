#!/usr/bin/env python3
"""
MSFT 문서에서 실제 Item 8 패턴 찾기
"""
import sys
import os
import re

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.edgar_report.edgar_report import EdgarReporterWrapper


def find_actual_item8_pattern():
    """MSFT 문서에서 실제 Item 8이 어떻게 나타나는지 찾기"""
    print("🔍 MSFT 문서에서 실제 Item 8 패턴 찾기")
    print("=" * 50)
    
    wrapper = EdgarReporterWrapper()
    
    # MSFT 문서 가져오기
    filing_data = wrapper.get_company_filings("MSFT")
    if not filing_data:
        print("❌ 파일링 데이터를 가져올 수 없습니다.")
        return
        
    recent_filings = filing_data['recent_filings']
    cik = filing_data['cik']
    
    latest_10k = None
    for i, form in enumerate(recent_filings['form']):
        if form == '10-K':
            latest_10k = {'accessionNumber': recent_filings['accessionNumber'][i]}
            break
    
    if not latest_10k:
        print("❌ 10-K 파일링을 찾을 수 없습니다.")
        return
        
    document_content = wrapper.get_10k_document_content(cik, latest_10k['accessionNumber'])
    if not document_content:
        print("❌ 문서 다운로드 실패")
        return
        
    print(f"✅ 문서 다운로드 성공: {len(document_content)} characters")
    
    # 1. "Financial" 키워드 모든 출현 위치 찾기
    print("\n1. 'Financial' 키워드 검색...")
    financial_matches = list(re.finditer(r'Financial', document_content, re.IGNORECASE))
    print(f"   'Financial' 발견: {len(financial_matches)} 개")
    
    # Financial 근처에서 Item 8 또는 8 패턴 찾기
    item8_candidates = []
    
    for match in financial_matches[:20]:  # 처음 20개만 확인
        start_pos = match.start()
        # 앞뒤 200자 확인
        context_start = max(0, start_pos - 200)
        context_end = min(len(document_content), start_pos + 200)
        context = document_content[context_start:context_end]
        
        # Item 8 또는 8 패턴이 있는지 확인
        if re.search(r'(?:Item\s*)?8\.?\s*Financial', context, re.IGNORECASE):
            item8_candidates.append({
                'pos': start_pos,
                'context': context.replace('\n', ' ').strip()
            })
    
    print(f"\n2. Item 8 관련 후보 발견: {len(item8_candidates)} 개")
    
    for i, candidate in enumerate(item8_candidates):
        print(f"\n후보 {i+1}: 위치 {candidate['pos']}")
        print(f"컨텍스트: ...{candidate['context'][:300]}...")
    
    # 3. 'STATEMENTS' 키워드로도 검색
    print("\n3. 'STATEMENTS' 키워드 검색...")
    statements_matches = list(re.finditer(r'STATEMENTS', document_content, re.IGNORECASE))
    print(f"   'STATEMENTS' 발견: {len(statements_matches)} 개")
    
    for match in statements_matches[:10]:  # 처음 10개만 확인
        start_pos = match.start()
        context_start = max(0, start_pos - 100)
        context_end = min(len(document_content), start_pos + 100)
        context = document_content[context_start:context_end]
        
        # 8이나 Item 8이 앞에 있는지 확인
        if re.search(r'(?:Item\s*)?8\.?\s*.*STATEMENTS', context, re.IGNORECASE):
            print(f"\n잠재적 Item 8: 위치 {start_pos}")
            context_clean = context.replace('\n', ' ').strip()
            print(f"컨텍스트: ...{context_clean}...")
    
    # 4. 더 넓은 패턴으로 검색
    print("\n4. 더 넓은 Item 8 패턴 검색...")
    
    broad_patterns = [
        r'8\.\s*[A-Z][a-z]+\s*[A-Z][a-z]+',  # 8. Financial Statements 형태
        r'ITEM\s*8',  # ITEM 8
        r'Item\s*8',  # Item 8
        r'8\..*Financial.*Statement',  # 8. ... Financial ... Statement
        r'Financial.*Statement.*Data',  # Financial ... Statement ... Data
        r'FINANCIAL.*STATEMENT.*DATA',  # 대문자 버전
    ]
    
    all_item8_matches = []
    
    for i, pattern in enumerate(broad_patterns):
        matches = list(re.finditer(pattern, document_content, re.IGNORECASE))
        print(f"   패턴 {i+1}: '{pattern}' → {len(matches)} 개")
        
        for match in matches[:3]:  # 각 패턴당 최대 3개만
            start_pos = match.start()
            end_pos = match.end()
            match_text = match.group()
            
            context_start = max(0, start_pos - 50)
            context_end = min(len(document_content), end_pos + 150)
            context = document_content[context_start:context_end]
            context_clean = re.sub(r'\s+', ' ', context).strip()
            
            all_item8_matches.append({
                'pattern': pattern,
                'start': start_pos,
                'end': end_pos,
                'text': match_text,
                'context': context_clean
            })
            
            print(f"     매치: '{match_text}' (위치: {start_pos})")
            print(f"     컨텍스트: ...{context_clean[:150]}...")
    
    print(f"\n5. 총 Item 8 관련 매치: {len(all_item8_matches)} 개")
    
    # 각 매치에 대해 실제 내용 추출 시도
    print("\n6. 각 매치에서 내용 추출 시도...")
    
    for i, match_info in enumerate(all_item8_matches):
        print(f"\n=== 매치 {i+1} 분석 ===")
        print(f"패턴: {match_info['pattern']}")
        print(f"매치 텍스트: '{match_info['text']}'")
        print(f"위치: {match_info['start']}-{match_info['end']}")
        
        # 이 위치부터 적당한 길이의 내용 추출
        start_pos = match_info['end']
        content = document_content[start_pos:start_pos+3000]  # 3000자까지
        
        # HTML 정리
        cleaned_content = wrapper.clean_html(f"<html><body>{content}</body></html>")
        word_count = len(cleaned_content.split())
        
        print(f"추출 내용: {len(cleaned_content)} chars, {word_count} words")
        print(f"미리보기: {cleaned_content[:200]}...")
        
        # Financial statements 키워드 확인
        financial_keywords = ['income statement', 'balance sheet', 'cash flow', 'revenue', 'net income']
        found_keywords = [kw for kw in financial_keywords if kw.lower() in cleaned_content.lower()]
        
        if found_keywords:
            print(f"✅ Financial 키워드 발견: {found_keywords}")
        else:
            print("❌ Financial 키워드 없음")
            
        if word_count > 50:
            print("✅ 충분한 내용량")
        else:
            print("❌ 내용량 부족")


if __name__ == "__main__":
    try:
        find_actual_item8_pattern()
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()