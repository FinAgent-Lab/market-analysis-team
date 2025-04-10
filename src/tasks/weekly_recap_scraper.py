import datetime
import hashlib
import os
from urllib.parse import urlparse

from dependency_injector.wiring import Provider
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    MilvusClient,
)
import pymilvus

from src.services.crawler_jpmorgan import CrawlerJPMorgan
from startup import Container
from src.utils.logger import setup_logger

logger = setup_logger("market_agent")


# @inject
def scrape_jp_weekly_recap(vector_store: Provider[Container.vector_store_recap]):
    url_prased = urlparse(os.getenv("MILVUS_URL_RECAP"))
    connections.connect(alias="default", host=url_prased.hostname, port=url_prased.port)

    content = CrawlerJPMorgan().get_weekly_recap_markdown()
    hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    logger.info("hash: %s", hash)

    create_collection_if_not_exists()
    collection = Collection(
        name=os.getenv("MILVUS_COLLECTION_NAME_RECAP", "weekly_recap")
    )
    collection.load()
    try:
        result = collection.query(
            expr=f'hash == "{hash}"',
            output_fields=["text"],
            limit=1,
        )
    except pymilvus.exceptions.MilvusException as e:
        error_code = e.code if hasattr(e, "code") else "unknown"
        if (
            not error_code == 1100
        ):  # Error code 1100 indicates that the item could not be found
            logger.info("Weekly recap already exists")
            raise e

    if len(result) > 0:
        logger.info("Weekly recap already exists")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(content)
    # 메타데이터 생성
    metadatas = [
        {"hash": hash, "created_at": datetime.datetime.now().isoformat()}
        for _ in range(len(chunks))
    ]

    vector_store.add_texts(chunks, metadatas=metadatas)
    logger.info("Weekly recap added to vector store")


def create_collection_if_not_exists():
    client = MilvusClient(uri=os.getenv("MILVUS_URL_RECAP"))

    collection_name = os.getenv("MILVUS_COLLECTION_NAME_RECAP", "weekly_recap")

    # 컬렉션 존재 여부 확인
    has_collection = pymilvus.utility.has_collection(collection_name)

    if not has_collection:
        # 컬렉션 스키마 정의
        fields = [
            FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="hash", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(
                name="created_at", dtype=DataType.VARCHAR, max_length=30
            ),  # ISO 형식 UTC 시간
            FieldSchema(
                name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536
            ),  # OpenAI text-embedding-3-small 모델의 차원
            FieldSchema(name="total_pages", dtype=DataType.INT64, nullable=True),
        ]
        schema = CollectionSchema(fields)

        # 컬렉션 생성
        client.create_collection(collection_name=collection_name, schema=schema)
        # collection = Collection(name=collection_name, schema=schema)

        # 인덱스 생성
        index_params = MilvusClient.prepare_index_params()
        _index_params = {
            "field_name": "vector",
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "index_name": "vector_index",
            "params": {"M": 8, "efConstruction": 64},
        }
        index_params.add_index(**_index_params)

        client.create_index(collection_name=collection_name, index_params=index_params)
