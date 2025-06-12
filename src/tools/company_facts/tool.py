import os
import requests
from typing import Dict, Any, Optional
from langchain_core.tools import BaseTool
from langchain_core.utils import get_from_dict_or_env
from pydantic import BaseModel, ConfigDict, SecretStr, model_validator, Field
from dotenv import load_dotenv

from src.data.models import CompanyFactsResponse

# 환경 변수 로드
load_dotenv()


class CompanyFactsAPIWrapper(BaseModel):
    """Wrapper for Financial Datasets API with secure API key handling."""
    
    financial_datasets_api_key: SecretStr
    
    model_config = ConfigDict(
        extra="forbid",
    )
    
    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: Dict) -> Dict:
        # 직접 환경 변수에서 가져오기 시도
        api_key = None
        
        # 여러 방법으로 API 키 시도
        if "financial_datasets_api_key" in values:
            api_key = values["financial_datasets_api_key"]
        elif "FINANCIAL_DATASETS_API_KEY" in values:
            api_key = values["FINANCIAL_DATASETS_API_KEY"]
        else:
            # 환경 변수에서 직접 가져오기
            api_key = os.getenv("FINANCIAL_DATASETS_API_KEY")
            if not api_key:
                # get_from_dict_or_env 사용
                api_key = get_from_dict_or_env(
                    values, "financial_datasets_api_key", "FINANCIAL_DATASETS_API_KEY"
                )
        
        if not api_key:
            raise ValueError(
                "Financial Datasets API key not found. "
                "Please set FINANCIAL_DATASETS_API_KEY environment variable or "
                "pass financial_datasets_api_key as a parameter."
            )
        
        values["financial_datasets_api_key"] = api_key
        return values
    
    def get_company_facts(self, ticker: str) -> str:
        """Financial Datasets API를 통한 회사 정보 조회"""
        try:
            api_key = self.financial_datasets_api_key.get_secret_value()
            headers = {"X-API-KEY": api_key}
            url = f"https://api.financialdatasets.ai/company/facts/?ticker={ticker}"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 401:
                return """
❌ **API Key 인증 실패**

제공된 FINANCIAL_DATASETS_API_KEY가 유효하지 않습니다.
GitHub Secrets에서 올바른 API 키가 설정되었는지 확인해주세요.
"""
            
            if response.status_code != 200:
                return f"❌ API 호출 실패: {response.status_code} - {response.text}"
            
            # 응답 파싱
            data = response.json()
            response_model = CompanyFactsResponse(**data)
            company_facts = response_model.company_facts
            
            if not company_facts:
                return f"❌ {ticker}에 대한 회사 정보를 찾을 수 없습니다. 올바른 티커 심볼인지 확인해주세요."
            
            return self._format_company_facts(company_facts.model_dump())
            
        except requests.exceptions.RequestException as e:
            return f"❌ 네트워크 오류: {str(e)}"
        except Exception as e:
            return f"❌ API 응답 처리 중 오류: {str(e)}"
    
    def _format_company_facts(self, facts: Dict[str, Any]) -> str:
        """회사 정보를 읽기 쉬운 형태로 포맷팅"""
        ticker = facts.get('ticker', 'N/A')
        name = facts.get('name', 'N/A')
        
        # 기본 정보
        basic_info = f"""
🏢 **{name} ({ticker}) 기업 정보**

📋 **기본 정보**
• 회사명: {name}
• 티커: {ticker}
• CIK: {facts.get('cik', 'N/A')}
• 거래소: {facts.get('exchange', 'N/A')}
• 상장일: {facts.get('listing_date', 'N/A')}
• 활성 상태: {'활성' if facts.get('is_active') else '비활성' if facts.get('is_active') is False else 'N/A'}
• 본사 위치: {facts.get('location', 'N/A')}
• 웹사이트: {facts.get('website_url', 'N/A')}
"""
        
        # 산업 분류
        industry_info = f"""
🏭 **산업 분류**
• 섹터: {facts.get('sector', 'N/A')}
• 산업: {facts.get('industry', 'N/A')}
• 카테고리: {facts.get('category', 'N/A')}
• SIC 코드: {facts.get('sic_code', 'N/A')}
• SIC 섹터: {facts.get('sic_sector', 'N/A')}
• SIC 산업: {facts.get('sic_industry', 'N/A')}
"""
        
        # 재무/시장 정보
        market_cap = facts.get('market_cap')
        if market_cap:
            if market_cap >= 1_000_000_000_000:  # 1조 달러
                market_cap_formatted = f"${market_cap/1_000_000_000_000:.2f}조"
            elif market_cap >= 1_000_000_000:  # 10억 달러
                market_cap_formatted = f"${market_cap/1_000_000_000:.2f}B"
            elif market_cap >= 1_000_000:  # 100만 달러
                market_cap_formatted = f"${market_cap/1_000_000:.2f}M"
            else:
                market_cap_formatted = f"${market_cap:,.0f}"
        else:
            market_cap_formatted = "N/A"
        
        employees = facts.get('number_of_employees')
        employees_formatted = f"{employees:,}명" if employees else "N/A"
        
        shares = facts.get('weighted_average_shares')
        shares_formatted = f"{shares:,}주" if shares else "N/A"
        
        financial_info = f"""
💰 **시장 및 재무 정보**
• 시가총액: {market_cap_formatted}
• 직원 수: {employees_formatted}
• 가중평균 발행주식수: {shares_formatted}
• SEC 공시 URL: {facts.get('sec_filings_url', 'N/A')}
"""
        
        # 전체 결과 조합
        result = basic_info + industry_info + financial_info
        
        # 추가 정보가 있으면 포함
        additional_notes = []
        
        if facts.get('sector') and facts.get('industry'):
            additional_notes.append(f"• {facts['sector']} 섹터의 {facts['industry']} 업종에 속합니다.")
        
        if market_cap and market_cap >= 200_000_000_000:  # 2000억 달러 이상
            additional_notes.append("• 대형주 (Large Cap) 기업입니다.")
        elif market_cap and market_cap >= 10_000_000_000:  # 100억 달러 이상
            additional_notes.append("• 중대형주 (Mid-Large Cap) 기업입니다.")
        elif market_cap and market_cap >= 2_000_000_000:  # 20억 달러 이상
            additional_notes.append("• 중소형주 (Small-Mid Cap) 기업입니다.")
        
        if employees and employees >= 100_000:
            additional_notes.append("• 대규모 기업으로 10만명 이상의 직원을 보유하고 있습니다.")
        elif employees and employees >= 10_000:
            additional_notes.append("• 중견 기업으로 1만명 이상의 직원을 보유하고 있습니다.")
        
        if additional_notes:
            result += f"""
📝 **추가 분석**
{chr(10).join(additional_notes)}
"""
        
        return result

class CompanyFactsTool(BaseTool):
    """회사 기본 정보 조회 도구"""
    
    name: str = "company_facts_search"
    description: str = (
        "Retrieve comprehensive company information including basic facts, "
        "market data, and business details for a given stock ticker. "
        "Input should be a valid stock ticker symbol (e.g., AAPL, MSFT, GOOGL)."
    )
    
    # Pydantic 필드로 선언
    api_wrapper: Optional[CompanyFactsAPIWrapper] = Field(default=None, exclude=True)
    init_error: Optional[str] = Field(default=None, exclude=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialize_api()
    
    def _initialize_api(self):
        """API Wrapper 초기화"""
        try:
            # 환경 변수 다시 로드
            load_dotenv()
            
            # 디버깅을 위한 환경 변수 확인
            api_key = os.getenv("FINANCIAL_DATASETS_API_KEY")
            print(f"🔍 Debug: FINANCIAL_DATASETS_API_KEY found: {'Yes' if api_key else 'No'}")
            if api_key:
                print(f"🔑 API Key preview: {api_key[:8]}...")
            
            # API Wrapper 초기화 (환경변수에서 자동으로 API 키 로드)
            self.api_wrapper = CompanyFactsAPIWrapper()
            print("✅ CompanyFactsAPIWrapper 초기화 성공")
            
        except Exception as e:
            print(f"❌ CompanyFactsAPIWrapper 초기화 실패: {e}")
            self.api_wrapper = None
            self.init_error = str(e)
    
    def _run(self, ticker: str) -> str:
        """회사 정보 조회 실행"""
        try:
            # 티커 정리
            ticker = ticker.strip().upper()
            
            # API Wrapper 초기화 확인
            if self.api_wrapper is None:
                error_msg = getattr(self, 'init_error', 'Unknown error')
                
                # 환경 변수 상태 확인
                env_status = f"""
🔧 **환경 변수 상태 확인:**
• FINANCIAL_DATASETS_API_KEY 존재: {'Yes' if os.getenv('FINANCIAL_DATASETS_API_KEY') else 'No'}
• 환경 변수 값 미리보기: {os.getenv('FINANCIAL_DATASETS_API_KEY', 'Not found')[:8]}...
• .env 파일 위치: {os.path.join(os.getcwd(), '.env')}
• .env 파일 존재: {'Yes' if os.path.exists('.env') else 'No'}
"""
                
                return f"""
❌ **API 초기화 실패**

Financial Datasets API 초기화 중 오류가 발생했습니다.

**오류 내용:** {error_msg}

{env_status}

**해결 방법:**
1. .env 파일에 FINANCIAL_DATASETS_API_KEY가 올바르게 설정되었는지 확인
2. 환경 변수 이름에 오타가 없는지 확인 (대소문자 구분)
3. API 키가 유효하고 활성화되어 있는지 확인
4. 애플리케이션 재시작 후 다시 시도

GitHub Secrets 설정 (배포 시):
• FINANCIAL_DATASETS_API_KEY = your_api_key_here
"""
            
            # API를 통한 회사 정보 조회
            return self.api_wrapper.get_company_facts(ticker)
                
        except Exception as e:
            return f"❌ 회사 정보 조회 중 오류 발생: {str(e)}"
    
    async def _arun(self, ticker: str) -> str:
        """비동기 실행 (동기 실행과 동일)"""
        return self._run(ticker)

# 하위 호환성을 위한 팩토리 함수
def create_company_facts_tool() -> CompanyFactsTool:
    """CompanyFactsTool 인스턴스를 생성하여 반환"""
    return CompanyFactsTool()
