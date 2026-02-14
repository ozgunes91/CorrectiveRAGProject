from typing import Any, Dict

from langchain_core.documents import Document
from langchain_tavily import TavilySearch
from graph.state import GraphState

web_search_tool = TavilySearch(k=3)

def web_search(state: GraphState) -> Dict[str, Any]:
    print("---WEB SEARCH---")
    question = state["question"]
    documents = state.get("documents") or []

    raw = web_search_tool.invoke(question)


    contents = []
    if isinstance(raw, dict) and isinstance(raw.get("results"), list):
        for r in raw["results"]:
            if isinstance(r, dict):
                title = r.get("title") or ""
                url = r.get("url") or ""
                content = r.get("content") or ""
                if content:
                    contents.append(f"{title}\n{url}\n{content}")
    else:
        contents.append(str(raw))

    web_text = "\n\n---\n\n".join(contents).strip()

    documents.append(
        Document(page_content=web_text, metadata={"source": "tavily", "query": question})
    )

    return {"documents": documents, "question": question, "web_search": True}
