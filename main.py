from dotenv import load_dotenv

load_dotenv()

from graph.graph import app

if __name__ == "__main__":
    print("Hello Advanced RAG")
    result = app.invoke({"question": "what are the Agents?"})
    print(result["generation"])