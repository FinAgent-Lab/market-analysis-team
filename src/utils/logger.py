import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = None) -> logging.Logger:
    """애플리케이션 로거를 설정합니다.

    Args:
        name (str, optional): 로거 이름. Defaults to None.

    Returns:
        logging.Logger: 설정된 로거 인스턴스
    """
    logger = logging.getLogger(name or __name__)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # 포맷터 설정
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (rotating)
    file_handler = RotatingFileHandler(
        "market_agent.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
