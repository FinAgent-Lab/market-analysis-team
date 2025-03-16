from typing import Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = "gpt-4o-mini"
    temperature: Optional[float] = 0.2


class QueryResponse(BaseModel):
    answer: str
    timestamp: str
