from abc import ABC, abstractmethod
from functools import wraps
import time
import os
from rich.console import Console

from src.models.do import RawResponse
from src.utils.logger import setup_logger
from langfuse.callback import CallbackHandler

console = Console()


def logging_node(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        console.print("\n" + "=" * (console.width))
        logger = setup_logger(f"market_agent.nodes.{self.__class__.__name__.lower()}")
        logger.info(f"Starting {self.__class__.__name__}...")

        start_time = time.time()

        # 함수 실행
        result = func(self, *args, **kwargs)

        end_time = time.time()
        execution_time = end_time - start_time

        logger.info(
            f"{self.__class__.__name__} completed successfully. "
            f"(실행 시간: {execution_time:.4f}초)"
        )
        console.print("=" * (console.width) + "\n")

        return result

    return wrapper


# TODO : singletone 로거 적용
# TODO : 에이전트의 기능 구현시 노드 내에서 완료 또는 노드+서비스


class Node(ABC):
    def __init__(self):
        self._instance = None
        self._logger_name = f"market_agent.nodes.{self.__class__.__name__.lower()}"
        self.logger = setup_logger(self._logger_name)
        self.DEFAULT_LLM_MODEL = "gpt-4o-mini"

        # Langfuse callback handler setup
        self.langfuse_enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"
        if self.langfuse_enabled:
            self._langfuse_handler = CallbackHandler(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
        else:
            self._langfuse_handler = None

    @logging_node
    def __call__(self, *args, **kwargs):
        return self._run(*args, **kwargs)

    @abstractmethod
    def _run(self, *args, **kwargs): ...

    @abstractmethod
    def _invoke(self, query: str) -> RawResponse: ...

    def invoke(self, query: str) -> RawResponse:
        return self._invoke(query)

    def _get_callback_config(self):
        """Get callback configuration for langchain operations"""
        if self.langfuse_enabled and self._langfuse_handler:
            return {"callbacks": [self._langfuse_handler]}
        return {}
