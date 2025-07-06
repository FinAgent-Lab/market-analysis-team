# us_financial.py
"""미국 주식 재무분석 노드 - 점수화 시스템 통합 버전"""

from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import logging
import datetime
import os

from src.graph.nodes.base import Node
from src.models.do import RawResponse
from src.tools.us_stock.tool import USFinancialStatementTool


class USFinancialAnalyzerNode(Node):
    def __init__(self):
        super().__init__()
        self.system_prompt = (
            "You are a financial statement analysis agent for US stocks. "
            "Your task is to analyze balance sheets, income statements, and financial ratios "
            "to provide a comprehensive assessment of a company's financial health, growth potential, and profitability. "
            "IMPORTANT SCORING REQUIREMENTS: "
            "- The analysis includes a comprehensive financial scoring system (0-100 points) with letter grades (A+ to D). "
            "- You MUST prominently display the financial scores throughout your analysis: "
            "  * Total Score: X/100 points (Grade) "
            "  * Profitability Score: X/100 points (Grade) "
            "  * Stability Score: X/100 points (Grade) "
            "  * Individual metric scores in respective sections (ROE, ROA, Operating Margin, Current Ratio, Debt-to-Equity) "
            "- Include scores alongside traditional metrics in profitability and stability sections. "
            "- Use the scoring system to enhance investment perspective: "
            "  * 90-100 points (A+): Exceptional - Highly recommended "
            "  * 80-89 points (A): Excellent - Recommended "
            "  * 70-79 points (B+): Good - Worth considering "
            "  * 60-69 points (B): Average - Careful review needed "
            "  * 50-59 points (C+): Below average - Improvement needed "
            "  * Below 50 (C-D): Weak - Caution required "
            "- Connect quantitative scores with qualitative analysis explanations. "
            "- Always highlight the overall financial score prominently in your response. "
            "- Maintain professional tone while making scores easily understandable for investors. "
            "Users can mention either a company name (like Apple, Microsoft) or a ticker symbol (like AAPL, MSFT). "
            "Present your findings clearly and concisely, but do not provide investment advice or recommendations. "
            "Only if no company name or ticker can be identified, ask for clarification. "
            "Always include the analyzed ticker symbol in your response using this format: 'Ticker: XXX'."
        )
        self.agent = None
        self.tools = [USFinancialStatementTool()]

        # 로깅 설정
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

    def _get_current_time(self) -> str:
        """현재 시간을 ISO 형식 문자열로 반환합니다."""
        return datetime.datetime.utcnow().isoformat()

    def _create_default_llm(self) -> ChatOpenAI:
        """환경변수를 사용하여 기본 LLM을 생성합니다."""
        return ChatOpenAI(
            model=os.getenv("MAIN_LLM_MODEL", "gpt-4o-mini"),
            temperature=0,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

    def _run(self, state: dict) -> Command:
        """LangGraph에서 호출되는 메인 실행 함수"""
        start_time = self._get_current_time()
        self.logger.info(f"[{start_time}] 재무분석 노드 실행 시작")

        try:
            # 에이전트 초기화
            if self.agent is None:
                assert state["llm"] is not None, "State에 llm이 포함되어야 합니다"
                llm = state["llm"]

                self.logger.info(f"에이전트 초기화: LLM 타입 = {type(llm).__name__}")

                # LLM을 도구에 전달
                self.tools[0].llm = llm

                self.agent = create_react_agent(
                    llm,
                    self.tools,
                    prompt=self.system_prompt,
                )
                self.logger.info("재무분석 에이전트 초기화 완료")

            # 사용자 메시지 처리
            user_message = state["messages"][-1].content
            safe_message = (
                user_message[:100] + "..." if len(user_message) > 100 else user_message
            )
            self.logger.info(f"사용자 쿼리 처리: '{safe_message}'")

            # 티커 심볼 추출 시도
            extracted_ticker = "unknown"
            try:
                extracted_ticker = self.tools[0]._extract_ticker(user_message)
                self.logger.info(f"추출된 티커: {extracted_ticker}")
            except Exception as e:
                self.logger.error(f"티커 추출 실패: {str(e)}")

            # 에이전트 실행
            self.logger.debug("재무분석 에이전트 실행 중...")
            agent_start_time = self._get_current_time()

            result = self.agent.invoke(state)
            analysis_text = result["messages"][-1].content

            agent_end_time = self._get_current_time()

            # 분석 결과 로깅 (미리보기만)
            log_preview = (
                analysis_text[:200] + "..."
                if len(analysis_text) > 200
                else analysis_text
            )
            self.logger.info(f"재무분석 완료 [{agent_start_time}~{agent_end_time}]")
            self.logger.debug(f"분석 결과 미리보기: {log_preview}")

            # 다음 단계로 전달할 명령 생성
            command = Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=analysis_text,
                            name="us_financial_analyzer",
                        )
                    ],
                    # 구조화된 분석 결과 저장
                    "financial_analysis": {
                        "ticker": extracted_ticker,
                        "market": "US",
                        "analysis_text": analysis_text,
                        "timestamp": self._get_current_time(),
                    },
                },
                goto="supervisor",
            )

            end_time = self._get_current_time()
            self.logger.info(f"[{end_time}] 재무분석 노드 실행 완료")
            return command

        except Exception as e:
            self.logger.error(
                f"재무분석 노드 실행 중 오류 발생: {str(e)}", exc_info=True
            )

            # 오류 발생 시에도 적절한 응답 반환
            error_message = f"재무분석 중 오류가 발생했습니다: {str(e)}"
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=error_message,
                            name="us_financial_analyzer",
                        )
                    ],
                    "financial_analysis": {
                        "ticker": "unknown",
                        "market": "US",
                        "analysis_text": error_message,
                        "error": str(e),
                        "timestamp": self._get_current_time(),
                    },
                },
                goto="supervisor",
            )

    def _invoke(self, query: str) -> RawResponse:
        """API를 통한 직접 호출 함수"""
        start_time = self._get_current_time()
        self.logger.info(f"[{start_time}] 직접 호출 시작")

        try:
            safe_query = query[:100] + "..." if len(query) > 100 else query
            self.logger.info(f"직접 호출 쿼리: '{safe_query}'")

            # 에이전트 초기화 (필요한 경우)
            agent = self.agent
            if agent is None:
                self.logger.debug("직접 호출용 에이전트 생성")
                default_llm = self._create_default_llm()

                # 도구에 LLM 설정
                self.tools[0].llm = default_llm

                agent = create_react_agent(
                    default_llm,
                    self.tools,
                    prompt=self.system_prompt,
                )

            # 도구에 LLM이 설정되지 않은 경우 설정
            if not hasattr(self.tools[0], "llm") or self.tools[0].llm is None:
                default_llm = self._create_default_llm()
                self.tools[0].llm = default_llm
                self.logger.debug("재무분석 도구에 기본 LLM 설정 완료")

            # 에이전트 실행 (콜백 없이 단순 실행)
            self.logger.debug("직접 호출로 에이전트 실행 중...")
            agent_start_time = self._get_current_time()

            # config = self._get_callback_config()
            # result = agent.invoke({"messages": [("human", query)]}, config=config)
            result = agent.invoke({"messages": [("human", query)]})
            response_content = result["messages"][-1].content

            agent_end_time = self._get_current_time()
            self.logger.info(
                f"직접 호출 완료 [{agent_start_time}~{agent_end_time}] "
                f"응답 길이: {len(response_content)}"
            )

            response = RawResponse(answer=response_content)

            end_time = self._get_current_time()
            self.logger.info(f"[{end_time}] 직접 호출 완료")
            return response

        except Exception as e:
            error_msg = f"재무분석 직접 호출 중 오류 발생: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            # 오류 응답 반환
            return RawResponse(
                answer=f"죄송합니다. 재무분석 중 오류가 발생했습니다: {str(e)}"
            )
