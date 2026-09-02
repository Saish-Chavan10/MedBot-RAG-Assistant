
import sys
sys.path.insert(0, ".")
from src.vectorstore import load_vectorstore, get_retriever
from src.RAG_chain import build_rag_chain, ask

print("Initializing your local MedBot components...")
vs = load_vectorstore()
retriever = get_retriever(vs)
chain = build_rag_chain(retriever)

print("\nAsking: What are the symptoms of malaria?\n")
result = ask(chain, "What are the symptoms of malaria?")

print("--- ANSWER ---")
print(result["answer"])
print("\n--- SOURCES ---")
for s in result["sources"]:
    print(f"Page {s[\"page\"]}: {s[\"preview\"]}")