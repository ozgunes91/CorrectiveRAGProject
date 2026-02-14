# CorrectiveRAGProject — Evidence‑First RAG with Guardrails (LangGraph)

This repo contains a **Corrective RAG** pipeline that routes a question, retrieves supporting context, optionally falls back to web search, and runs graders to reduce hallucinations before returning an answer.

The core idea: **answers should be backed by evidence (documents) or the system should decline / retry**.

---

## What it does

Given an input question, the workflow (LangGraph) follows this pattern:

1) **Route** the question (RAG vs Web Search)
2) **Retrieve** documents from a local vector store (Chroma)
3) **Grade** retrieved documents for relevance
4) If evidence is insufficient, **Web Search** (Tavily) and append results as a `Document`
5) **Generate** an answer
6) **Grade** the generation:
   - grounded in documents?
   - answers the question?

> You will see these steps in the console logs (e.g., `---ROUTE QUESTION---`, `---RETRIEVE---`, `---WEB SEARCH---`, etc.).

---

## Repository structure (as used by the code)

- `main.py`  
  Runs a sample invocation: loads env and calls `app.invoke({"question": ...})`.

- `ingestion.py`  
  Builds/loads a **Chroma** collection persisted under `./.chroma` and exposes a `retriever`.

- `graph/graph.py`  
  Builds and compiles the **LangGraph** state machine (the app is imported as `from graph.graph import app`).

- `graph/state.py`  
  Graph state (typed dict / schema) used by nodes.

- `graph/nodes/`  
  Node functions used by the graph (examples in this repo include `retrieve`, `grade_documents`, `web_search`, `generate`).

- `graph/chains/`  
  Prompt + LLM “chains” and graders (router, relevance grader, hallucination grader, etc.).

---

## Requirements

- Python **3.11+**
- Environment variables:
  - `OPENAI_API_KEY` (embeddings + LLM)
  - `TAVILY_API_KEY` (web search)
  - Optional: `USER_AGENT` (recommended for some HTTP-based loaders)

---

## Install

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the packages used by the project (based on imports in the code):

```bash
pip install -U   python-dotenv   langgraph   langchain-openai   langchain-chroma   langchain-tavily   langchain-community   langchain-text-splitters   chromadb
```

> If you later add a `requirements.txt`, you can replace the above with `pip install -r requirements.txt`.

---

## Configure environment variables

Create a `.env` file in the repo root (do **not** commit it):

```bash
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
# Optional but recommended:
USER_AGENT=corrective-ragproject/1.0
```

---

## Build / refresh the local vector store (Chroma)

`ingestion.py` is where the URL sources are loaded, chunked, embedded, and persisted to `./.chroma`.

Run:

```bash
python ingestion.py
```

After this, you should have a `./.chroma/` directory containing the persisted collection.

---

## Run

Run the demo entrypoint:

```bash
python main.py
```

`main.py` loads `.env`, imports the compiled graph app, and invokes it with a question.

---

## Notes on data sources

There are **two evidence paths**:

1) **Curated corpus (Chroma)**  
   Your `ingestion.py` defines which URLs (or loaders) are indexed into the local store.

2) **Live web fallback (Tavily)**  
   When the graph decides retrieval evidence is insufficient, it queries Tavily and converts results into a `langchain_core.documents.Document` appended to the evidence list.

---

## Common warnings you may see

- **Structured output warning (`json_schema` vs `function_calling`)**  
  Some models (e.g., `gpt-3.5-turbo`) don’t support OpenAI Structured Outputs via `json_schema`.  
  Use `method="function_calling"` when creating structured graders.

- **Chroma / Tavily deprecation warnings**  
  Prefer the split packages:
  - `from langchain_chroma import Chroma`
  - `from langchain_tavily import TavilySearch`

- **`USER_AGENT environment variable not set`**  
  Set `USER_AGENT` in `.env` to silence the warning.

---

## Suggested next steps (productization)

If you want this to look like a “mini product” on GitHub:

- Add a `streamlit_app.py` (chat UI + sources panel + route badges)
- Standardize output schema:
  - `answer`, `route`, `grounded`, `answers_question`, `sources[]`
- Add `eval/` with a small test set and a simple report:
  - grounding pass rate
  - answer pass rate
- Add `.gitignore` (exclude `.env`, `.venv/`, `.chroma/`, caches)

---

## License

Choose a license that matches your intent (MIT is common for demos).

