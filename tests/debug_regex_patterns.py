#!/usr/bin/env python3
"""
정규식 패턴 디버깅 스크립트
"""
import re

def test_regex_patterns():
    """정규식 패턴 테스트"""
    
    # 샘플 텍스트 (실제 10-K에서 나타나는 형식들)
    sample_text = """
    FORM 10-K
    
    TABLE OF CONTENTS
    Item 1. Business .......................... 5
    Item 1A. Risk Factors .................... 15
    Item 7. Management's Discussion .......... 45
    
    Item 1. Business
    Apple Inc. (the "Company") designs, manufactures, and markets smartphones...
    
    Item 1A. Risk Factors
    The Company's business, reputation, results of operations...
    
    Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
    The following discussion should be read in conjunction...
    
    Item 8. Financial Statements and Supplementary Data
    See Note 1, "Summary of Significant Accounting Policies"...
    """
    
    print("🔍 정규식 패턴 디버깅")
    print("=" * 50)
    
    # 기존 패턴들
    patterns = {
        "Item 1. Business": r"^\s*Item\s+1\.\s*Business",
        "Item 1A. Risk Factors": r"^\s*Item\s+1A\.\s*Risk\s*Factors", 
        "Item 7. Management's Discussion and Analysis": r"^\s*Item\s+7\.\s*Management's\s*Discussion\s*and\s*Analysis",
        "Item 8. Financial Statements and Supplementary Data": r"^\s*Item\s+8\.\s*Financial\s*Statements\s*and\s*Supplementary\s*Data",
    }
    
    print("📋 기존 패턴 테스트:")
    for pattern_name, pattern in patterns.items():
        matches = list(re.finditer(pattern, sample_text, re.IGNORECASE | re.MULTILINE))
        print(f"\n{pattern_name}:")
        print(f"  패턴: {pattern}")
        print(f"  매치 수: {len(matches)}")
        
        for i, match in enumerate(matches):
            print(f"  매치 {i+1}: 위치 {match.start()}-{match.end()}")
            print(f"    내용: '{sample_text[match.start():match.end()]}'")
            
            # 매치 후 200자까지 내용 확인
            content_after = sample_text[match.end():match.end()+200].strip()
            print(f"    이후 내용: '{content_after[:100]}...'")
    
    print("\n" + "="*50)
    print("🔧 개선된 패턴 테스트:")
    
    # 더 유연한 패턴들
    improved_patterns = {
        "Item 1. Business": r"Item\s+1\.\s*Business",
        "Item 1A. Risk Factors": r"Item\s+1A\.\s*Risk\s*Factors",
        "Item 7. Management's Discussion": r"Item\s+7\.\s*Management['\u2019s]*\s*Discussion",
        "Item 8. Financial Statements": r"Item\s+8\.\s*Financial\s*Statements",
    }
    
    for pattern_name, pattern in improved_patterns.items():
        matches = list(re.finditer(pattern, sample_text, re.IGNORECASE))
        print(f"\n{pattern_name}:")
        print(f"  패턴: {pattern}")
        print(f"  매치 수: {len(matches)}")
        
        for i, match in enumerate(matches):
            print(f"  매치 {i+1}: 위치 {match.start()}-{match.end()}")
            print(f"    내용: '{sample_text[match.start():match.end()]}'")
            
            # 매치 후 내용 확인
            content_after = sample_text[match.end():match.end()+200].strip()
            print(f"    이후 내용: '{content_after[:100]}...'")
    
    print("\n" + "="*50)
    print("🎯 실제 SEC 문서 형식 테스트:")
    
    # 실제 SEC 문서에서 나타나는 다양한 형식들
    real_sec_formats = [
        "Item 1.\tBusiness",
        "Item 1. Business",
        "Item 1.Business",
        "ITEM 1. BUSINESS",
        "Item 1A. Risk Factors",
        "Item 1A.\tRisk Factors",
        "ITEM 1A. RISK FACTORS",
        "Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations",
        "Item 7.\tManagement's Discussion and Analysis",
        "Item 8. Financial Statements and Supplementary Data",
        "Item 8.\tFinancial Statements and Supplementary Data",
    ]
    
    # 가장 유연한 패턴
    flexible_patterns = {
        "Item 1": r"Item\s+1\.?\s*Business",
        "Item 1A": r"Item\s+1A\.?\s*Risk\s*Factors", 
        "Item 7": r"Item\s+7\.?\s*Management['\u2019]*s?\s*Discussion",
        "Item 8": r"Item\s+8\.?\s*Financial\s*Statements",
    }
    
    print("실제 형식들:")
    for format_text in real_sec_formats:
        print(f"  '{format_text}'")
        
        for pattern_name, pattern in flexible_patterns.items():
            if re.search(pattern, format_text, re.IGNORECASE):
                print(f"    ✅ {pattern_name} 패턴 매치")
            else:
                print(f"    ❌ {pattern_name} 패턴 미매치")
        print()


def test_next_item_detection():
    """다음 Item 감지 테스트"""
    print("\n🔍 다음 Item 감지 테스트")
    print("=" * 50)
    
    sample_content = """
    Item 1. Business
    
    Apple Inc. (the "Company") designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories, and sells a range of related services. The Company's customers are primarily in the consumer, small and mid-sized business, education, enterprise and government markets.
    
    The Company sells its products worldwide through its retail stores, online stores, and direct sales force, as well as through third-party cellular network carriers, wholesalers, retailers, and resellers.
    
    Item 1A. Risk Factors
    
    The Company's business, reputation, results of operations, financial condition and stock price can be affected by a number of factors.
    
    Item 2. Properties
    
    The Company's headquarters are located in Cupertino, California.
    """
    
    # Item 1 시작 위치 찾기
    item1_pattern = r"Item\s+1\.\s*Business"
    match = re.search(item1_pattern, sample_content, re.IGNORECASE)
    
    if match:
        start_pos = match.end()
        print(f"Item 1 시작 위치: {match.start()}-{match.end()}")
        print(f"Item 1 매치 텍스트: '{match.group()}'")
        
        # 다음 Item 찾기
        next_item_pattern = r"Item\s+\d+[A-Z]?\."
        next_match = re.search(next_item_pattern, sample_content[start_pos:], re.IGNORECASE)
        
        if next_match:
            end_pos = start_pos + next_match.start()
            print(f"다음 Item 위치: {start_pos + next_match.start()}-{start_pos + next_match.end()}")
            print(f"다음 Item 텍스트: '{next_match.group()}'")
            
            # Item 1 내용 추출
            item1_content = sample_content[start_pos:end_pos].strip()
            print(f"\nItem 1 추출 내용 길이: {len(item1_content)}")
            print(f"Item 1 내용:\n{item1_content}")
            
        else:
            print("다음 Item을 찾을 수 없음")
    else:
        print("Item 1을 찾을 수 없음")


if __name__ == "__main__":
    test_regex_patterns()
    test_next_item_detection()