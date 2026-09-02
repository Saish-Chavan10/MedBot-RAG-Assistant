import sys
from pathlib import Path
from typing import Any, Dict, List

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import (
    OLLAMA_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    MAX_TOKENS_RESPONSE
)

from src.logger import get_logger
log = get_logger(__name__)

Prompt_Template = """
You are MedBot, an expert medical assistant built on the Gale Encyclopedia of Medicine (3rd edition).
You help doctors and medical professionals get accurate, well-structured medical information instantly.

RULES:
- Answer ONLY from the provided context below.
- Use proper medical terminology.
- Structure your answer clearly: always start with a brief definition, then cover causes, symptoms, diagnosis, and treatment where relevant.
- If the context does not have enough information, say: "I don't have sufficient information in the encyclopedia to answer this accurately."
- Never fabricate or guess medical facts.
- Be thorough but precise. Doctors value accuracy over brevity.

CONTEXT FROM ENCYCLOPEDIA:
__________________________________________
{context}
__________________________________________
QUESTION: {input}

ANSWER: 
"""
PROMPT = PromptTemplate(
    template=Prompt_Template,
    # Note: Modern chains require 'input' instead of 'question'
    input_variables=["context", "input"]
)

def get_llm() -> ChatOllama:
    return ChatOllama(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        num_predict=MAX_TOKENS_RESPONSE, # Fixed max_tokens -> num_predict for Ollama
        base_url=OLLAMA_BASE_URL         # Fixed ollam_base_url -> base_url
    )

def build_rag_chain(retriever):
    llm = get_llm()
    
    # 1. Create the chain that formats the prompt with the retrieved docs
    question_answer_chain = create_stuff_documents_chain(llm, PROMPT)
    
    # 2. Combine the retriever with the QA chain
    chain = create_retrieval_chain(retriever, question_answer_chain)
    
    log.info(f"RAG chain built [model={LLM_MODEL}, temp={LLM_TEMPERATURE}]")
    return chain

def ask(chain, question: str) -> Dict[str, Any]:
    if not question.strip():
        return {"answer": "Please provide a valid question", "sources": []}
    
    log.info(f"Question: {question[:80]}")

    # Modern chains invoke using "input" instead of "query"
    result = chain.invoke({"input": question})
    
    # Modern chains return the answer under "answer", not "result"
    answer = result.get("answer", "No answer generated.")
    
    # Modern chains return docs under "context", not "source_documents"
    source_docs: List = result.get("context", [])

    seen = set()
    sources = []
    for doc in source_docs:
        page = doc.metadata.get("page", "?")
        if page not in seen:
            seen.add(page)
            sources.append({
                "page": page,
                "preview": doc.page_content[:150].replace("\n", " ") + "...",
            })

    log.info(f"Answer generated | sources: pages {[s['page'] for s in sources]}")

    return {
        "answer": answer,
        "sources": sources
    }

def build_streaming_chain(retriever):
    llm = ChatOllama(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        num_predict=MAX_TOKENS_RESPONSE,
        base_url=OLLAMA_BASE_URL,
        # LangChain handles streaming differently now, but we enable it on the model level here
        streaming=True 
    )

    question_answer_chain = create_stuff_documents_chain(llm, PROMPT)
    chain = create_retrieval_chain(retriever, question_answer_chain)

    log.info("Streaming RAG Chain is built")
    return chain