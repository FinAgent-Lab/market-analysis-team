#!/usr/bin/env python3
"""
재무제표 표 형식 개선 테스트
"""
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.edgar_report.edgar_report import EdgarReporterWrapper


def test_financial_table_formatting():
    """재무제표 표 형식 개선 테스트"""
    print("🧪 재무제표 표 형식 개선 테스트")
    print("=" * 50)
    
    wrapper = EdgarReporterWrapper()
    
    # 현재 MSFT Item 8 결과 테스트
    print("1. MSFT Item 8 개선된 형식으로 테스트...")
    result = wrapper.analyze_company_report("MSFT", "10-K")
    
    # Item 8 부분만 추출
    item8_start = result.find("#### Item 8. Financial Statements and Supplementary Data")
    if item8_start != -1:
        item8_end = result.find("### 🔗 추가 정보", item8_start)
        if item8_end != -1:
            item8_section = result[item8_start:item8_end]
            
            print("개선된 Item 8 형식:")
            print("-" * 60)
            print(item8_section)
            print("-" * 60)
            
            # 표 형식이 개선되었는지 확인
            content_start = item8_section.find("```") + 3
            content_end = item8_section.rfind("```")
            if content_start > 2 and content_end > content_start:
                content = item8_section[content_start:content_end]
                
                # 숫자 정렬 확인
                lines = content.split('\n')
                table_lines = [line for line in lines if '$' in line or any(c.isdigit() for c in line)]
                
                print(f"\n표 형식 분석:")
                print(f"- 전체 줄 수: {len(lines)}")
                print(f"- 표 데이터 줄 수: {len(table_lines)}")
                
                if len(table_lines) > 0:
                    print("- 표 데이터 예시:")
                    for i, line in enumerate(table_lines[:5]):  # 처음 5줄만
                        print(f"  {i+1}: {line}")
                
        else:
            print("Item 8 섹션의 끝을 찾을 수 없습니다.")
    else:
        print("Item 8 섹션을 찾을 수 없습니다.")


def test_table_formatting_logic():
    """표 형식 로직 직접 테스트"""
    print("\n🔧 표 형식 로직 직접 테스트")
    print("=" * 50)
    
    wrapper = EdgarReporterWrapper()
    
    # 샘플 재무제표 데이터
    sample_table_data = """
AND SUPPLEMENTARY DATAINCOME STATEMENTS
(In millions, except per share amounts)
Year Ended June 30,
2025
2024
2023
Revenue:
Product
$
63,946
$
64,773
$
64,699
Service and other
217,778
180,349
147,216
Total revenue
281,724
245,122
211,915
Cost of revenue:
Product
13,501
15,272
17,804
Service and other
74,330
58,842
48,059
Total cost of revenue
87,831
74,114
65,863
Gross margin
193,893
171,008
146,052
Net income
$
101,832
$
88,136
$
72,361
"""
    
    print("원본 데이터:")
    print("-" * 40)
    print(sample_table_data)
    print("-" * 40)
    
    print("\n표 형식 개선 적용...")
    formatted_data = wrapper._format_financial_table(sample_table_data)
    
    print("\n개선된 데이터:")
    print("-" * 40)
    print(formatted_data)
    print("-" * 40)
    
    # 개선 효과 분석
    original_lines = sample_table_data.strip().split('\n')
    formatted_lines = formatted_data.strip().split('\n')
    
    print(f"\n개선 효과 분석:")
    print(f"- 원본 줄 수: {len(original_lines)}")
    print(f"- 개선 후 줄 수: {len(formatted_lines)}")
    
    # 숫자가 포함된 줄 수 계산
    original_number_lines = sum(1 for line in original_lines if any(c.isdigit() for c in line))
    formatted_number_lines = sum(1 for line in formatted_lines if any(c.isdigit() for c in line))
    
    print(f"- 원본 숫자 포함 줄: {original_number_lines}")
    print(f"- 개선 후 숫자 포함 줄: {formatted_number_lines}")


def test_apple_financial_table():
    """Apple 재무제표도 테스트"""
    print("\n🍎 Apple 재무제표 표 형식 테스트")
    print("=" * 50)
    
    wrapper = EdgarReporterWrapper()
    
    print("Apple Item 8 테스트...")
    result = wrapper.analyze_company_report("Apple", "10-K")
    
    # Item 8 부분만 추출
    item8_start = result.find("#### Item 8. Financial Statements and Supplementary Data")
    if item8_start != -1:
        item8_end = result.find("### 🔗 추가 정보", item8_start)
        if item8_end != -1:
            item8_section = result[item8_start:item8_end]
            
            print("Apple Item 8 결과:")
            print("-" * 60)
            print(item8_section[:1000])  # 처음 1000자만
            print("..." if len(item8_section) > 1000 else "")
            print("-" * 60)
            
        else:
            print("Apple Item 8 섹션의 끝을 찾을 수 없습니다.")
    else:
        print("Apple Item 8 섹션을 찾을 수 없습니다.")


if __name__ == "__main__":
    try:
        test_financial_table_formatting()
        test_table_formatting_logic()
        test_apple_financial_table()
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()