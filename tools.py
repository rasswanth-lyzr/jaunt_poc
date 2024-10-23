from duckduckgo_search import DDGS
from lyzr_agent.tools.annotation import tool


@tool(
    name="duckduckgo_search",
    description="Searches for results in DuckDuckGo web search and returns 5 results",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to use in DuckDuckGo web search",
            }
        },
        "required": ["query"],
    },
)
def duckduckgo_search_tool(query: str) -> str:
    try:
        results = DDGS().text(query, max_results=5)
        return results
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return f"An error occurred: {str(e)}"
