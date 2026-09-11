"""
verify_output.py

Standalone checker for a generated case study. Confirms the Day 10
pipeline output is well-formed and genuinely evidence-grounded:

  1. final JSON has the right top-level shape
  2. all six sections are present, in order
  3. every section has {content, evidence, confidence}
  4. confidence label matches the insight-count rule
     (0 -> Weak Evidence, 1 -> Low, 2-3 -> Medium, 4+ -> High)
  5. evidence is capped at 3 snippets and never exceeds the insight count
  6. every evidence chunk_id actually exists in the saved chunks
  7. each evidence snippet really comes from its source chunk (not invented)

Usage:
    python verify_output.py            # defaults to zerodha
    python verify_output.py nykaa
"""

import json
import re
import sys

from src.config import CASE_STUDIES_DIR, INSIGHTS_DIR, CLEANED_DATA_DIR
from src.references import determine_confidence

SECTION_ORDER = ["Background", "Challenge", "Strategy", "Execution", "Results", "Learning"]


def _norm(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def verify(company):
    company = company.lower()
    ok = True

    def check(label, condition, detail=""):
        nonlocal ok
        mark = "PASS" if condition else "FAIL"
        if not condition:
            ok = False
        line = f"  [{mark}] {label}"
        if detail and not condition:
            line += f"  -> {detail}"
        print(line)

    final_p = CASE_STUDIES_DIR / f"{company}_case_study_with_evidence.json"
    insights_p = INSIGHTS_DIR / f"{company}_insights.json"
    chunks_p = CLEANED_DATA_DIR / f"{company}_chunks.json"

    print(f"\nVerifying '{company}'")
    for p in (final_p, insights_p, chunks_p):
        if not p.exists():
            print(f"  [FAIL] missing file: {p}")
            print("\nRESULT: FAIL (generate the case study first)\n")
            return False

    final = json.load(open(final_p, encoding="utf-8"))
    insights = json.load(open(insights_p, encoding="utf-8"))
    chunks = json.load(open(chunks_p, encoding="utf-8"))

    chunk_index = {c["chunk_id"]: c["text"] for c in chunks}

    # 1 + 2
    check("top-level has company_name + case_study",
          "company_name" in final and "case_study" in final)
    cs = final.get("case_study", {})
    check("all six sections present, in order",
          list(cs.keys()) == SECTION_ORDER, f"got {list(cs.keys())}")

    for name in SECTION_ORDER:
        sec = cs.get(name, {})
        insight_count = len(insights.get(name.lower(), []))

        # 3
        check(f"{name}: has content/evidence/confidence",
              {"content", "evidence", "confidence"} <= set(sec.keys()))

        # 4
        expected = determine_confidence(len(sec.get("evidence", [])), insight_count)
        check(f"{name}: confidence '{sec.get('confidence')}' matches {insight_count} insights",
              sec.get("confidence") == expected, f"expected {expected}")

        evidence = sec.get("evidence", [])
        # 5
        check(f"{name}: evidence count {len(evidence)} <= 3 and <= insights({insight_count})",
              len(evidence) <= 3 and len(evidence) <= insight_count)

        for ev in evidence:
            cid = ev.get("chunk_id")
            # 6
            check(f"{name}: chunk_id {cid} exists in chunks",
                  cid in chunk_index, "not found")
            # 7
            if cid in chunk_index:
                snippet_core = _norm(ev.get("snippet", "").rstrip(". "))[:120]
                grounded = snippet_core and snippet_core in _norm(chunk_index[cid])
                check(f"{name}: snippet is real text from {cid}",
                      grounded, "snippet not found in source chunk")

    print(f"\nRESULT: {'PASS' if ok else 'FAIL'}\n")
    return ok


if __name__ == "__main__":
    company = sys.argv[1] if len(sys.argv) > 1 else "zerodha"
    sys.exit(0 if verify(company) else 1)