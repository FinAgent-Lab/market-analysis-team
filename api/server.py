from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.route import router as api_router


class APIBuilder:
    def __init__(self):
        self.app = None

    def __build(self):
        self.app = FastAPI(
            title="Market Analysis API",
            description="주식 시장 분석을 위한 AI 에이전트 네트워크 API",
            version="0.1.0",
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.app.include_router(api_router)

    def create_app(self) -> FastAPI:
        self.__build()
        return self.app
