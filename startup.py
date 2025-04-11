import os

from dependency_injector import containers, providers
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_milvus import Milvus

from src.graph.builder import SupervisorGraphBuilder
from src.utils.logger import setup_logger


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    logger = providers.Singleton(setup_logger, "market_agent")

    supervisor_graph = providers.Singleton(SupervisorGraphBuilder)

    llm = providers.Singleton(ChatOpenAI, model="gpt-4o-mini", temperature=0)

    embeddings = providers.Singleton(OpenAIEmbeddings, model="text-embedding-3-small")

    vector_store_recap = providers.Singleton(
        Milvus,
        embedding_function=embeddings,
        connection_args={
            "uri": os.getenv("MILVUS_URL_RECAP"),
            "db_name": os.getenv("MILVUS_DB_NAME_RECAP", "default"),
        },
        collection_name=os.getenv("MILVUS_COLLECTION_NAME_RECAP", "weekly_recap"),
        auto_id=True,
    )

    # app = providers.Factory(APIBuilder)
    # for node in supervisor_graph.get_nodes():
    #     app.add_route(f"/{node.name.lower().replace('node', '')}", "POST", lambda x: node.invoke(x))
    # app.create_app()
