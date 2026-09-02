import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


import os
import sys
import json
import time
import warnings
from pathlib import Path

import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    Faithfulness,
    ResponseRelevancy,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
    SemanticSimilarity,
)
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import LLM_MODEL
from src.vectorstore import load_vectorstore, get_retriever
from src.RAG_chain import build_rag_chain

# ---------------- settings ----------------
RUN_NAME = "baseline"      # <-- change to "v2" after you improve MedBot
LIMIT = None               # e.g. 3 for a quick smoke test
SLEEP_BETWEEN = 30         # raise to 45 if you see 429 errors
USE_PRECISION = True       # False saves ~40% of judge tokens
MAX_CHARS_CHUNK = 700
MAX_CHARS_RESPONSE = 1200
# ------------------------------------------

HERE = Path(__file__).parent
CACHE_PATH = HERE / f"inference_cache_{RUN_NAME}.json"
REPORT_PATH = HERE / f"report_{RUN_NAME}.csv"
LLM_COLS = ["faithfulness", "answer_relevancy",
            "llm_context_precision_with_reference", "context_recall"]


def run_inference(test_cases):
    rows = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else []
    if len(rows) >= len(test_cases):
        print(f"Loaded full cache ({len(rows)} rows)")
        return rows
    print(f"Inference: resuming from question {len(rows) + 1}")

    rag_chain = build_rag_chain(get_retriever(load_vectorstore()))

    for idx, item in enumerate(test_cases, 1):
        if idx <= len(rows):
            continue
        q = item.get("user_input") or item.get("question") or item.get("query")
        gt = item.get("reference") or item.get("ground_truth")
        if not q or not gt:
            raise KeyError(f"Missing question/ground truth in item {idx}: {item.keys()}")

        print(f"  [{idx}/{len(test_cases)}] {q}")
        for attempt in range(5):
            try:
                result = rag_chain.invoke({"input": q})
                break
            except Exception as e:
                print(f"      retry {attempt + 1}/5: {type(e).__name__}")
                time.sleep(5 * (attempt + 1))
        else:
            print("      giving up; rerun to resume")
            break

        rows.append({
            "user_input": q,
            "response": result.get("answer", ""),
            "retrieved_contexts": [d.page_content for d in result.get("context", [])],
            "reference": gt,
        })
        CACHE_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def shrink(r):
    return {
        "user_input": r["user_input"],
        "response": r["response"][:MAX_CHARS_RESPONSE],
        "retrieved_contexts": [c[:MAX_CHARS_CHUNK] for c in r["retrieved_contexts"]],
        "reference": r["reference"],
    }


def run_evaluation():
    print(f"Run: {RUN_NAME} | App model: {LLM_MODEL}")
    golden = json.loads((HERE / "golden_dataset.json").read_text(encoding="utf-8"))
    if LIMIT:
        golden = golden[:LIMIT]
    rows = run_inference(golden)

    judge = "openai/gpt-oss-20b"
    make_llm = lambda tokens: LangchainLLMWrapper(
        ChatGroq(model=judge, temperature=0, max_tokens=tokens,
                 reasoning_effort="low", max_retries=0),
        bypass_n=True,  # Groq rejects n>1
    )
    llm = make_llm(1500)
    faith_llm = make_llm(3500)  # faithfulness needs more output room (fixes NaN)

    emb = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"))

    metrics = [
        Faithfulness(llm=faith_llm),
        ResponseRelevancy(llm=llm, embeddings=emb, strictness=1),
        LLMContextRecall(llm=llm),
        SemanticSimilarity(embeddings=emb),
    ]
    #if USE_PRECISION:
        #metrics.insert(2, LLMContextPrecisionWithReference(llm=llm))

    USE_PRECISION = False

    cfg = RunConfig(max_workers=1, timeout=300, max_retries=8, max_wait=60)

    # resume: keep only fully scored rows, redo the rest
    done = set()
    if REPORT_PATH.exists():
        prev = pd.read_csv(REPORT_PATH)
        cols = [c for c in LLM_COLS if c in prev.columns]
        ok = prev.dropna(subset=cols)
        ok.to_csv(REPORT_PATH, index=False)
        done = set(ok["user_input"])
        print(f"Resuming: {len(done)} rows already scored")

    todo = [r for r in rows if r["user_input"] not in done]
    print(f"{len(todo)} samples to evaluate\n")

    for i, r in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {r['user_input']}")
        try:
            res = evaluate(dataset=Dataset.from_list([shrink(r)]), metrics=metrics,
                           llm=llm, embeddings=emb, run_config=cfg,
                           raise_exceptions=False, show_progress=False)
            df = res.to_pandas()
            df["user_input"] = r["user_input"]
            df.to_csv(REPORT_PATH, mode="a", header=not REPORT_PATH.exists(), index=False)
            print("   ", {k: round(float(df[k].iloc[0]), 3)
                          for k in LLM_COLS + ["semantic_similarity"]
                          if k in df.columns and pd.notna(df[k].iloc[0])})
        except Exception as e:
            print(f"   FAILED: {e}")
            if "429" in str(e) or "rate_limit" in str(e).lower():
                print("   Rate limit hit. Rerun later; it resumes.")
                break
        if i < len(todo):
            time.sleep(SLEEP_BETWEEN)

    final = pd.read_csv(REPORT_PATH)
    print("\n=== MEAN SCORES ===")
    print(final[[c for c in LLM_COLS + ["semantic_similarity"] if c in final.columns]].mean().round(3))
    print("\nNaN per metric:")
    print(final[[c for c in LLM_COLS if c in final.columns]].isna().sum())
    print(f"\nSaved to {REPORT_PATH}")

    cols_present = [c for c in LLM_COLS if c in df.columns]
    if df[cols_present].isna().any(axis=1).iloc[0]:
        fails += 1
        if fails >= 2:
            print("Two incomplete rows in a row: likely the daily limit. Stopping; rerun later.")
            break
    else:
        fails = 0


if __name__ == "__main__":
    run_evaluation()