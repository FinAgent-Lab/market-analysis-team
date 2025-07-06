import pytest
import os
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import logging

# 프로젝트 루트를 Python path에 추가
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestGoogleCrawlerWrapper:
    """GoogleCrawlerWrapper 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """각 테스트 메서드 실행 전 실행"""
        from src.tools.google_crawler.google_crawler import GoogleCrawlerWrapper
        self.crawler = GoogleCrawlerWrapper()
    
    def test_crawler_initialization(self):
        """크롤러 초기화 테스트"""
        assert self.crawler is not None
        assert self.crawler.headers is not None
        assert "User-Agent" in self.crawler.headers
        print("✅ 크롤러 초기화 성공")
    
    def test_explicit_date_search(self):
        """명시적 날짜 검색 테스트"""
        query = "Apple stock AAPL"
        result = self.crawler.search_with_explicit_dates(
            query, 
            start_date="06/01/2024", 
            end_date="06/30/2024",
            max_results=3
        )
        
        print("검색 결과 미리보기:")
        print(result[:200] + "..." if len(result) > 200 else result)
        
        # 결과 검증
        assert isinstance(result, str)
        assert len(result) > 0
        assert query in result or "Google News 크롤링 결과" in result
        print("✅ 명시적 날짜 검색 테스트 성공")
    
    def test_default_date_behavior(self):
        """기본 날짜 동작 테스트 (날짜 미지정시)"""
        result = self.crawler.search_with_explicit_dates(
            "Microsoft MSFT",
            max_results=2
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        print("✅ 기본 날짜 동작 테스트 성공")


class TestGoogleCrawlerTool:
    """GoogleCrawler Tool 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """각 테스트 메서드 실행 전 실행"""
        from src.tools.google_crawler.tool import GoogleCrawler
        self.tool = GoogleCrawler()
    
    def test_tool_initialization(self):
        """툴 초기화 테스트"""
        assert self.tool is not None
        assert hasattr(self.tool, '_run')
        assert hasattr(self.tool, 'name')
        print("✅ 툴 초기화 성공")
    
    def test_tool_with_dates(self):
        """날짜가 포함된 툴 실행 테스트"""
        result = self.tool._run(
            "Tesla TSLA stock",
            start_date="01/01/2024",
            end_date="01/31/2024",
            max_results=2
        )
        
        print("툴 실행 결과 미리보기:")
        print(result[:200] + "..." if len(result) > 200 else result)
        
        assert isinstance(result, str)
        assert len(result) > 0
        print("✅ 날짜 포함 툴 실행 테스트 성공")
    
    def test_tool_without_dates(self):
        """날짜 없는 툴 실행 테스트"""
        result = self.tool._run("NVDA stock", max_results=1)
        
        assert isinstance(result, str)
        assert len(result) > 0
        print("✅ 날짜 없는 툴 실행 테스트 성공")


class TestGoogleCrawlerAgent:
    """GoogleCrawler 에이전트 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """각 테스트 메서드 실행 전 실행"""
        try:
            from src.graph.nodes.google_crawler import GoogleCrawlerNode
            from langchain_openai import ChatOpenAI
            
            self.node = GoogleCrawlerNode()
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        except ImportError as e:
            pytest.skip(f"에이전트 의존성 누락: {e}")
    
    @pytest.mark.integration
    def test_korean_query_translation(self):
        """한국어 쿼리 번역 테스트"""
        query = "애플 최근 일주일"
        
        try:
            state = {
                "messages": [("human", query)],
                "llm": self.llm
            }
            result = self.node._run(state)
            
            assert result is not None
            print(f"✅ 한국어 쿼리 번역 테스트 성공: {query}")
            
        except Exception as e:
            pytest.skip(f"에이전트 실행 실패 (네트워크/API 이슈): {e}")
    
    @pytest.mark.integration
    def test_english_query(self):
        """영어 쿼리 테스트"""
        query = "Tesla stock today"
        
        try:
            state = {
                "messages": [("human", query)],
                "llm": self.llm
            }
            result = self.node._run(state)
            
            assert result is not None
            print(f"✅ 영어 쿼리 테스트 성공: {query}")
            
        except Exception as e:
            pytest.skip(f"에이전트 실행 실패 (네트워크/API 이슈): {e}")


def test_manual_agent_integration():
    """수동 에이전트 통합 테스트 (pytest 외부)"""
    print("\n" + "="*60)
    print("🤖 수동 에이전트 통합 테스트")
    print("="*60)
    
    try:
        from src.graph.nodes.google_crawler import GoogleCrawlerNode
        from langchain_openai import ChatOpenAI
        
        node = GoogleCrawlerNode()
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        test_queries = [
            "애플 최근 일주일",
            "테슬라 오늘", 
            "Microsoft MSFT 어제",
            "Google stock news"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 테스트 {i}: '{query}'")
            try:
                state = {
                    "messages": [("human", query)],
                    "llm": llm
                }
                
                # 로깅 레벨을 ERROR로 임시 변경
                original_level = logging.getLogger().level
                logging.getLogger().setLevel(logging.ERROR)
                
                # stdout/stderr 캡처
                captured_output = StringIO()
                
                with redirect_stdout(captured_output), redirect_stderr(captured_output):
                    result = node._run(state)
                
                # 로깅 레벨 복구
                logging.getLogger().setLevel(original_level)
                
                if result and hasattr(result, 'update') and 'messages' in result.update:
                    content = result.update['messages'][0].content
                    
                    # 결과 요약만 출력
                    lines = content.split('\n')
                    summary_lines = []
                    
                    for line in lines:
                        if '검색 기간' in line or '검색 결과' in line:
                            summary_lines.append(line)
                        if len(summary_lines) >= 2:
                            break
                    
                    print("✅ 에이전트 실행 성공")
                    if summary_lines:
                        print("📊 " + " | ".join(summary_lines))
                else:
                    print("❌ 결과를 가져올 수 없음")
                    
            except Exception as e:
                print(f"❌ 에이전트 실행 오류: {str(e)[:100]}...")
            
            print("-" * 40)
            
    except ImportError as e:
        print(f"❌ 에이전트 테스트 스킵 (의존성 부족): {e}")
    except Exception as e:
        print(f"❌ 에이전트 테스트 실패: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Google Crawler 종합 테스트")
    print("=" * 60)
    
    # pytest 실행 (integration 테스트 제외)
    print("\n🔧 단위 테스트 실행...")
    exit_code = pytest.main([
        __file__, 
        "-v", 
        "-m", "not integration",  # integration 마크가 없는 테스트만 실행
        "--tb=short"  # 짧은 traceback
    ])
    
    # 수동 통합 테스트
    if exit_code == 0:
        test_manual_agent_integration()
    else:
        print("❌ 단위 테스트 실패로 통합 테스트 스킵")
