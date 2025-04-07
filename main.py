from dotenv import load_dotenv

from dependency_injector.wiring import Provide, inject
import uvicorn

from api.server import APIBuilder
from src.graph.nodes import (
    NaverNewsSearcherNode,
    ReportAssistantNode,
    ChosunRSSFeederNode,
    WSJEconomyRSSFeederNode,
    WSJMarketRSSFeederNode,
    GoogleSearcherNode,
    USFinancialAnalyzerNode
)
from src.utils.logger import setup_logger
from src.graph.builder import SupervisorGraphBuilder
from startup import Container
from rich.console import Console

console = Console()
load_dotenv(override=True)
logger = setup_logger("market_agent")
logo = """
[cyan]
==============================================================================================

███████ ██ ███    ██  █████   ██████  ███████ ███    ██ ████████       ██       █████  ██████  
██      ██ ████   ██ ██   ██ ██       ██      ████   ██    ██          ██      ██   ██ ██   ██ 
█████   ██ ██ ██  ██ ███████ ██   ███ █████   ██ ██  ██    ██    █████ ██      ███████ ██████  
██      ██ ██  ██ ██ ██   ██ ██    ██ ██      ██  ██ ██    ██          ██      ██   ██ ██   ██ 
██      ██ ██   ████ ██   ██  ██████  ███████ ██   ████    ██          ███████ ██   ██ ██████  
                                                                                               
----------------------------------------------------------------------------------------------
                __  __          _       _                    _         _    
                |  \/  |__ _ _ _| |_____| |_   __ _ _ _  __ _| |_  _ __(_)___
                | |\/| / _` | '_| / / -_)  _| / _` | ' \/ _` | | || (_-< (_-
                |_|  |_\__,_|_| |_\_\___|\__| \__,_|_||_\__,_|_|\_, /__/_/__/
                                                                |__/         
----------------------------------------------------------------------------------------------
# MEMBER(가나다 순)
- 전병훈 (팀장)
- 강동석
- 백인걸
- 엄창용        https://github.com/e7217
- 왕수연
- 장현상
----------------------------------------------------------------------------------------------
                                                    Since 2025.03.04, Let's study together!
==============================================================================================
"""


@inject
def main(
        graph_builder: SupervisorGraphBuilder = Provide[Container.supervisor_graph],
):
    console.print(logo)
    logger.info("Starting Market Analysis Agent service...")

    ## 그래프 빌더
    """
    에이전트 노드를 이곳에 추가해주세요.
    노드 추가 시, 다음의 기능을 동적으로 적용하게됩니다.
    - supervisor 노드에 멤버로 등록
    - 노드 이름을 기반으로 API 엔드포인트 생성(예: SampleNone -> /api/sample)
    
    Example:
    graph_builder.add_node(NewNode())
    """
    graph_builder.add_node(NaverNewsSearcherNode())
    graph_builder.add_node(GoogleSearcherNode())
    graph_builder.add_node(ReportAssistantNode())
    graph_builder.add_node(ChosunRSSFeederNode())
    graph_builder.add_node(WSJEconomyRSSFeederNode())
    graph_builder.add_node(WSJMarketRSSFeederNode())

    # 한투 API 분석 에이전트 노드 주석 처리 (미국 주식 노드로 대체)
    # graph_builder.add_node(HantooFinancialAnalyzerNode())

    # 미국 주식 분석 에이전트 노드 추가 (Alpha Vantage API 사용)
    graph_builder.add_node(USFinancialAnalyzerNode())

    graph_builder.build()

    ## API 서버 빌더
    api_builder = APIBuilder()
    app = api_builder.create_app()
    for node in graph_builder.get_nodes():
        app.add_api_route(
            f"/api/{node.__class__.__name__.lower().replace('node', '')}",
            methods=["POST"],
            endpoint=node.invoke,
        )

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    container = Container()
    container.wire(modules=["api.route"])
    container.wire(modules=[__name__])
    main()