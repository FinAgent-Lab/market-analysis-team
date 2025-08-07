from typing import Optional
from langchain_core.tools import BaseTool
from pydantic import Field
from src.tools.edgar_report.edgar_report import EdgarReporterWrapper


class EdgarReporterResults(BaseTool):
    """SEC EDGAR report analyzer tool"""
    
    name: str = "edgar_reporter_results_json"
    description: str = (
        "A SEC EDGAR report analysis tool that retrieves and analyzes 10-K and 10-Q reports "
        "for US public companies. Useful for analyzing company business information, "
        "financial disclosures, and regulatory filings. "
        "Input should be a company identifier (name, ticker, or CIK) with optional report type. "
        "Parameters: company_identifier (required), report_type (10-K or 10-Q, default: 10-K). "
        "Returns detailed company information, recent filings, and business section analysis."
    )
    
    # Pydantic 필드로 선언
    api_wrapper: Optional[EdgarReporterWrapper] = Field(default=None, exclude=True)
    init_error: Optional[str] = Field(default=None, exclude=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialize_wrapper()
    
    def _initialize_wrapper(self):
        """Wrapper 초기화"""
        try:
            self.api_wrapper = EdgarReporterWrapper()
        except Exception as e:
            self.api_wrapper = None
            self.init_error = str(e)
    
    def _run(
        self, 
        company_identifier: str,
        report_type: str = "10-K",
        **kwargs
    ) -> str:
        """SEC 보고서 분석 실행"""
        try:
            # Wrapper 초기화 확인
            if self.api_wrapper is None:
                error_msg = getattr(self, 'init_error', 'Unknown error')
                return f"""
❌ **Edgar Reporter 초기화 실패**

SEC EDGAR API 초기화 중 오류가 발생했습니다.

**오류 내용:** {error_msg}

**해결 방법:**
1. 네트워크 연결 상태 확인
2. SEC EDGAR API 접근 권한 확인
3. User-Agent 설정 확인

관리자에게 문의하여 EDGAR API 설정을 확인해주세요.
"""
            
            # 보고서 분석 수행
            return self.api_wrapper.analyze_company_report(company_identifier, report_type)
                
        except Exception as e:
            return f"❌ SEC EDGAR 보고서 분석 중 오류 발생: {str(e)}"
    
    async def _arun(self, company_identifier: str, report_type: str = "10-K", **kwargs) -> str:
        """비동기 실행 (동기 실행과 동일)"""
        return self._run(company_identifier, report_type, **kwargs)


class EdgarReporter(EdgarReporterResults):
    """Main SEC EDGAR report analyzer tool"""
    
    name: str = "edgar_reporter"
    description: str = (
        "A SEC EDGAR report analysis tool for US public companies. "
        "Analyzes 10-K and 10-Q reports to extract business information, "
        "company details, and recent filings. "
        "Parameters: company_identifier (required - company name, ticker, or CIK), "
        "report_type (10-K or 10-Q, default: 10-K). "
        "Automatically handles company lookup and returns formatted analysis results."
    )


# 하위 호환성을 위한 팩토리 함수
def create_edgar_reporter_tool() -> EdgarReporter:
    """EdgarReporter 인스턴스를 생성하여 반환"""
    return EdgarReporter()