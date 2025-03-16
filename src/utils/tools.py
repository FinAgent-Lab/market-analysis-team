from langchain_community.tools.tavily_search import TavilySearchResults

# TODO : 더 깔끔한 방식 고려


class ToolSet:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._tools = []
            self._web_search = None
            self._initialized = True

    @property
    def tools(self):
        return self._tools

    @tools.setter
    def tools(self, value):
        self._tools = value

    @property
    def web_search(self):
        if self._web_search is None:
            self._web_search = TavilySearchResults(max_results=2)
        return self._web_search

    def get_tools(self):
        return self.tools

    def get_tool_names(self):
        return [tool.name for tool in self.tools]
