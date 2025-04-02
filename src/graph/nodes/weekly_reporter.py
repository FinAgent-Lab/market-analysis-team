from langchain_milvus import Milvus
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


from src.graph.nodes.base import Node
from src.models.do import RawResponse


class WeeklyReporterNode(Node):
    def __init__(
        self,
        vector_store: Milvus,
    ):
        super().__init__()
        self.retriever = vector_store.as_retriever()
        template = """
You are a weekly reporter that reports the weekly market recap of JPMorgan.
Please answer the following question based on the given context. 
Try to find the answer strictly within the context. If an exact answer is not available, provide any relevant or similar information from the context that might be helpful. 
If the context does not contain any relevant information at all, respond with: "There is not enough information to answer the question."

- Keep your answer clear and concise.
- Include all referenced sources (such as date, responder, and link) in your response.

Context:
{context}

Question:
{query}

Answer:"""
        self.prompt = ChatPromptTemplate.from_template(template)
        self.chain = None
        self.llm = None

    def _run(self, state: dict) -> dict:
        assert state["llm"] is not None, "The State model should include llm"
        # self.llm = state["llm"]
        self.logger.info(f"state: {state}")
        self.logger.info(f"query: {state['messages'][-1].content}")
        result = self._get_chain().invoke(state["messages"][-1].content)
        self.logger.info(f"   result: {result}")
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=result,
                        name=self.__class__.__name__.lower().replace("node", ""),
                    )
                ]
            },
            goto="supervisor",
        )

    def _invoke(self, query: str) -> RawResponse:
        result = self._get_chain().invoke(query)
        return RawResponse(answer=result)

    def _get_chain(self):
        if not self.llm:
            self.llm = ChatOpenAI(model=self.DEFAULT_LLM_MODEL)
        if not self.chain:
            self.chain = (
                {"context": self.retriever, "query": RunnablePassthrough()}
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
        return self.chain
