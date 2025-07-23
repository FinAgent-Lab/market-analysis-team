# Stage 1: 의존성 설치
FROM python:3.11-slim as builder

WORKDIR /app

# 빌드에 필요한 시스템 패키지만 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN pip install --no-cache-dir uv

# 의존성 파일만 먼저 복사 (캐시 활용)
COPY pyproject.toml uv.lock ./

# 의존성 설치 (개발 의존성 제외)
RUN uv sync --no-dev

# Stage 2: 최종 런타임 이미지
FROM python:3.11-slim

WORKDIR /app

# 런타임에 필요한 최소한의 패키지만 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/cache/apt/*

# uv만 설치 (캐시 없이)
RUN pip install --no-cache-dir uv

# 빌더 스테이지에서 가상환경만 복사
COPY --from=builder /app/.venv /app/.venv

# 애플리케이션 코드 복사
COPY . /app

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 포트 설정
EXPOSE 8000

# 실행 명령 (uv 사용)
CMD ["uv", "run", "main.py"]
