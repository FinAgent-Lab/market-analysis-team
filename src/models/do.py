from pydantic import BaseModel


class RawResponse(BaseModel):
    answer: str
