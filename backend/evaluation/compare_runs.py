from pathlib import Path
import pandas as pd

HERE = Path(__file__).parent

cols = ["faithfulness", "answer_relevancy", "llm_context_precision_with_reference",
        "context_recall", "semantic_similarity"]

a = pd.read_csv(HERE / "report_baseline.csv")
b = pd.read_csv(HERE / "report_v2.csv")

# compare only questions that were scored in both runs
common = set(a.user_input) & set(b.user_input)
a = a[a.user_input.isin(common)]
b = b[b.user_input.isin(common)]

out = pd.DataFrame({"baseline": a[cols].mean(), "v2": b[cols].mean()})
out["delta"] = out["v2"] - out["baseline"]

print(f"Questions compared: {len(common)}")
print(out.round(3))