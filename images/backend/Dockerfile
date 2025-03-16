# Python 3.11 베이스 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry 대신 uv 설치
RUN pip install uv

# 프로젝트 파일 복사
COPY . /app

# 의존성 설치
RUN uv sync

# 포트 설정
EXPOSE 8000

# 실행 명령
CMD ["uv", "run", "main.py"]
