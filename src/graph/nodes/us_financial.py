from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
import logging
import datetime
import os
from langsmith import Client
from langsmith.run_helpers import traceable as trace_run

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
            "Users can mention either a company name (like Apple, Microsoft) or a ticker symbol (like AAPL, MSFT). "
            "Present your findings clearly and concisely, but do not provide investment advice or recommendations. "
            "Only if no company name or ticker can be identified, ask for clarification. "
            "Always include the analyzed ticker symbol in your response using this format: 'Ticker: XXX'."
        )
        self.agent = None
        self.tools = [USFinancialStatementTool()]

        # Configure logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

        # LangSmith 설정
        try:
            # LangSmith API 키 설정 확인
            if "LANGSMITH_API_KEY" not in os.environ:
                self.logger.warning(
                    "LANGSMITH_API_KEY 환경 변수가 설정되지 않았습니다. LangSmith 추적이 비활성화됩니다."
                )
                self.langsmith_enabled = False
            else:
                # LangSmith 클라이언트 초기화
                self.client = Client()
                self.langsmith_enabled = True
                self.logger.info("LangSmith 클라이언트 초기화 성공")
        except Exception as e:
            self.logger.warning(f"LangSmith 클라이언트 초기화 실패: {str(e)}")
            self.langsmith_enabled = False

    def _get_current_time(self) -> str:
        """현재 시간을 ISO 형식 문자열로 반환합니다."""
        return datetime.datetime.utcnow().isoformat()

    # LangSmith 추적 데코레이터 적용
    @trace_run(name="us_financial_analyzer_run")
    def _run(self, state: dict) -> Command:
        start_time = self._get_current_time()
        self.logger.info(f"[{start_time}] 실행 시작: _run 메소드")

        try:
            # Initialize agent if needed
            if self.agent is None:
                assert state["llm"] is not None, "The State model should include llm"
                llm = state["llm"]

                # Log LLM initialization
                self.logger.info(f"에이전트 초기화 중: LLM 타입 = {type(llm).__name__}")

                # LLM 참조를 도구의 속성에 추가
                self.tools[0].llm = llm

                self.logger.debug(
                    "ReAct 에이전트 생성 중 (도구 및 시스템 프롬프트 설정)"
                )
                self.agent = create_react_agent(
                    llm,
                    self.tools,
                    prompt=self.system_prompt,
                )
                self.logger.info("에이전트 초기화 완료")

            # 사용자 메시지 추출
            user_message = state["messages"][-1].content
            safe_message = (
                user_message[:100] + "..." if len(user_message) > 100 else user_message
            )
            self.logger.info(f"사용자 쿼리 처리 중: '{safe_message}'")

            # Extract ticker symbol
            self.logger.debug("티커 심볼 추출 시도 중")
            try:
                extracted_ticker = self.tools[0]._extract_ticker(user_message)

                ticker_extraction_success = True
                self.logger.info(f"티커 추출 결과: {extracted_ticker}")
                self.logger.info(f"티커 추출 성공 여부: {ticker_extraction_success}")
            except Exception as e:
                ticker_extraction_success = False
                extracted_ticker = None
                error_msg = f"티커 추출 실패: {str(e)}"
                self.logger.error(error_msg)
                self.logger.error(f"티커 추출 성공 여부: {ticker_extraction_success}")

            # Execute agent
            self.logger.debug("금융 분석 에이전트 실행 중")
            agent_start_time = self._get_current_time()

            try:
                # Execute agent
                result = self.agent.invoke(state)

                # Get analysis content
                analysis_text = result["messages"][-1].content

                # Truncate log output to prevent overwhelming logs
                log_analysis_preview = (
                    analysis_text[:200] + "..."
                    if len(analysis_text) > 200
                    else analysis_text
                )
                agent_end_time = self._get_current_time()
                self.logger.info(
                    f"금융 분석 완료, 결과 미리보기: \n{log_analysis_preview}"
                )
                self.logger.debug(
                    f"에이전트 실행 시간: {agent_start_time} ~ {agent_end_time}"
                )

            except Exception as e:
                error_msg = f"에이전트 실행 실패: {str(e)}"
                self.logger.error(error_msg)
                # Re-raise to be handled by the graph
                raise

            # Use extracted ticker or set as unknown
            ticker = extracted_ticker if extracted_ticker else "unknown"
            self.logger.info(f"최종 사용 티커: {ticker}")

            # Create command for next step
            command = Command(
                update={
                    "messages": [
                        HumanMessage(
                            content=analysis_text,
                            name="us_financial_analyzer",
                        )
                    ],
                    # Store analysis results in structured format
                    "financial_analysis": {
                        "ticker": ticker,
                        "market": "US",
                        "analysis_text": analysis_text,
                    },
                },
                goto="supervisor",
            )

            end_time = self._get_current_time()
            self.logger.info(f"[{end_time}] _run 메소드 실행 완료")
            return command

        except Exception as e:
            self.logger.error(f"_run 메소드에서 오류 발생: {str(e)}", exc_info=True)
            # Re-raise for proper error handling in the graph
            raise

    # LangSmith 추적 데코레이터 적용
    @trace_run(name="us_financial_analyzer_invoke")
    def _invoke(self, query: str) -> RawResponse:
        start_time = self._get_current_time()
        self.logger.info(f"[{start_time}] 직접 호출 시작: _invoke 메소드")

        try:
            safe_query = query[:100] + "..." if len(query) > 100 else query
            self.logger.info(f"쿼리로 직접 호출: '{safe_query}'")

            # Initialize agent if needed
            agent = self.agent
            if agent is None:
                self.logger.debug("직접 호출을 위한 새 에이전트 생성 중")
                default_llm = ChatOpenAI(model=self.DEFAULT_LLM_MODEL)

                agent = create_react_agent(
                    default_llm,
                    self.tools,
                    prompt=self.system_prompt,
                )

            # Set LLM in tool if needed
            if not hasattr(self.tools[0], "llm") or self.tools[0].llm is None:
                default_llm = ChatOpenAI(model=self.DEFAULT_LLM_MODEL)
                self.tools[0].llm = default_llm
                self.logger.debug(
                    f"금융 도구에 기본 LLM 설정: {self.DEFAULT_LLM_MODEL}"
                )

            # Execute agent
            self.logger.debug("직접 쿼리로 에이전트 실행 중")
            agent_start_time = self._get_current_time()

            result = agent.invoke({"messages": [("human", query)]})
            response_content = result["messages"][-1].content

            agent_end_time = self._get_current_time()
            self.logger.info(
                f"직접 호출 완료: {agent_start_time} ~ {agent_end_time}, 응답 길이: {len(response_content)}"
            )

            response = RawResponse(answer=response_content)

            end_time = self._get_current_time()
            self.logger.info(f"[{end_time}] _invoke 메소드 실행 완료")
            return response

        except Exception as e:
            error_msg = f"_invoke 메소드에서 오류 발생: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            # Return error response
            return RawResponse(answer=f"금융 분석 중 오류가 발생했습니다: {str(e)}")
