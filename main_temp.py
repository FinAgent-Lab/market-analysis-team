from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from market_agent import create_agent_graph  # 너가 만든 Agent Graph 함수

app = FastAPI()

class QueryRequest(BaseModel):
    query: str  # 사용자 질문

executor = create_agent_graph()
print(f"들고온 그래프: {executor}")

@app.post("/agent")
async def run_agent(request: QueryRequest):
    try:
        user_input = request.query  # 입력된 질문 가져오기
        result = executor.invoke({"message": [HumanMessage(content=user_input)]})  # Agent 실행
        return {"result": result}  # 결과 반환
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Financial Agent API is running."}
