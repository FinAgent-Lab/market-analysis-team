import hashlib
import os
from urllib.parse import urlparse

from dependency_injector.wiring import inject, Provider
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from pymilvus import connections, Collection
import pymilvus

from src.services.crawler_jpmorgan import CrawlerJPMorgan
from src.services.duplicate_checker import DuplicateChecker
from startup import Container


# @inject
def scrape_jp_weekly_recap(vector_store: Provider[Container.vector_store_recap]):
    
    url_prased = urlparse(os.getenv("MILVUS_URL_RECAP"))
    connections.connect(alias="default", host=url_prased.hostname, port=url_prased.port)
    collection = Collection(os.getenv("MILVUS_COLLECTION_NAME_RECAP", "weekly_recap"))
    
    content = CrawlerJPMorgan().get_weekly_recap()

    query_option = {
        "query": "dummy",
        "k": 1,
        "filter": {
            "hash": hashlib.sha256(content).hexdigest()
        }
    }

    print("hash: ", hashlib.sha256(content).hexdigest())    
    # result = vector_store.similarity_search(**query_option)
    # print("scrape_jp_weekly_recap result: ", result)
    
    collection.load()
    try:
        result = collection.query(
            expr=f'hash == "{hashlib.sha256(content).hexdigest()}"',
            output_fields=["text"],
            limit=1,
        )
    except pymilvus.exceptions.MilvusException as e:
        print("scrape_jp_weekly_recap error: ", e)
        result = []
    
    print("scrape_jp_weekly_recap result: ", result)
    
    if len(result) > 0:
        return
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(content)

    print("scrape_jp_weekly_recap chunks: ", chunks)

    # vector_store.add_texts(chunks)
