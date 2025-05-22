from typing import Optional
from pydantic import BaseModel
import os


class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = os.getenv("MAIN_LLM_MODEL", "gpt-4o-mini")
    temperature: Optional[float] = 0.2


class QueryResponse(BaseModel):
    answer: str
    timestamp: str
