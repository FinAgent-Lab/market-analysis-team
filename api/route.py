from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
import datetime as dt
from langchain_openai import ChatOpenAI

from dependency_injector.wiring import inject, Provide

from startup import Container
from src.graph.builder import BuilderABC
from src.models.graph_state import SupervisorState
from src.utils.logger import setup_logger
from api.models import QueryRequest, QueryResponse

# 로거 설정
logger = setup_logger("market_agent.routes")

router = APIRouter(prefix="/api")


@router.get("/")
async def root():
    """API 상태 확인 엔드포인트"""
    return {"status": "online", "message": "Market Analysis Agent API is running"}


@router.get("/health")
async def health_check():
    """시스템 상태 확인 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": dt.datetime.now().isoformat(),
    }


# TODO: 의존성 주입 방식이 적절치 않아보임.
@router.post("/query", response_model=QueryResponse)
@inject
async def process_query(
    request: QueryRequest,
    graph: Annotated[BuilderABC, Depends(Provide[Container.supervisor_graph])],
    llm: Annotated[ChatOpenAI, Depends(Provide[Container.llm])],
):
    """
    사용자 쿼리를 처리하고 에이전트 네트워크의 응답을 반환합니다.
    """
    try:
        if not graph:
            raise HTTPException(
                status_code=500, detail="그래프가 초기화되지 않았습니다."
            )

        logger.info(f"Received query: {request.query}")

        # LLM 인스턴스 생성
        _llm = llm.bind(**request.model_dump())
        #  ChatOpenAI(model=request.model, temperature=request.temperature)

        # 그래프 실행
        state = SupervisorState(llm=_llm, messages=[("user", request.query)])
        answer = graph.execute(state)

        logger.info(f"Generated answer for query: {request.query}")

        # 응답 생성
        response = QueryResponse(
            answer=answer["messages"][-1].content,
            timestamp=dt.datetime.now().isoformat(),
        )

        return response

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
