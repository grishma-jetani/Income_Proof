"""
Integration test for the full pipeline.
Run from backend/ with: python test_pipeline.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.services.analytics.stability_metrics import compute_stability
from app.services.categorization.llm_categorizer import apply_llm_categories, categorize_with_llm
from app.services.categorization.rules import categorize_batch_rules
from app.services.normalization.authenticity import verify_pdf_authenticity
from app.services.normalization.normalize import check_balance_continuity, normalize
from app.services.parsing.csv_parser import parse_phonepe_csv
from app.services.parsing.pdf_parser import parse_pdf

CSV_PATH = "../data/sample_statements/phonepe_export_jan_apr_2026.csv"
BOI_PDF_PATH = "../data/sample_statements/boi_statement_jan_apr_2026.pdf"
TAMPERED_PDF_PATH = "../data/sample_statements/boi_statement_TAMPERED.pdf"


def divider(label: str):
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print("=" * 60)


def test_file(label: str, filepath: str, is_csv: bool = False):
    divider(label)

    if not os.path.exists(filepath):
        print(f"  FILE NOT FOUND: {filepath}")
        print("  Run data/synthetic_generator/main.py first.")
        return

    # Authenticity check (PDFs only)
    if not is_csv:
        auth = verify_pdf_authenticity(filepath)
        signal = auth.get("overall_signal", "unknown")
        print(f"\nAuthenticity signal:  {signal.upper()}")
        print(f"Explanation:          {auth.get('overall_explanation', '')}")
        for chk in auth.get("checks", []):
            result = (
                "✅ PASS" if chk["passed"] is True
                else "❌ FAIL" if chk["passed"] is False
                else "—  N/A"
            )
            print(f"  {result}  {chk['check']}: {chk['detail'][:80]}")

    # Parse
    if is_csv:
        raw = parse_phonepe_csv(filepath)
        fmt = "upi_csv"
    else:
        raw, fmt = parse_pdf(filepath)
        print(f"\nDetected format:      {fmt}")

    print(f"Raw transactions:     {len(raw)}")

    # Normalize
    normalized = normalize(raw)
    print(f"After normalization:  {len(normalized)}")

    # Balance continuity
    continuity = check_balance_continuity(normalized)
    status = (
        "✅ PASSED"
        if continuity["passed"]
        else f"❌ FAILED ({len(continuity['issues'])} issue(s))"
    )
    print(f"Balance continuity:   {status}")
    if not continuity["passed"] and continuity["issues"]:
        issue = continuity["issues"][0]
        print(
            f"  First issue → row {issue['row']}: "
            f"expected ₹{issue['expected']}, "
            f"printed ₹{issue['actual']}, "
            f"discrepancy ₹{issue['discrepancy']}"
        )

    # Categorize
    after_rules = categorize_batch_rules(normalized)
    uncat = [t for t in after_rules if t["category"] is None]
    print(f"Rules categorized:    {len(after_rules) - len(uncat)}")
    print(f"Needs LLM:            {len(uncat)}")

    if uncat:
        llm_mapping = categorize_with_llm(uncat)
        after_rules = apply_llm_categories(after_rules, llm_mapping)
        print(f"LLM categorized:      {len(uncat)}")

    cats: dict[str, int] = {}
    for t in after_rules:
        c = t.get("category") or "Personal / Other"
        cats[c] = cats.get(c, 0) + 1
    print("\nCategory breakdown:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:<35} {count}")

    # Stability metrics
    metrics = compute_stability(after_rules)
    factor_detail = metrics.pop("_factor_detail", {})
    factor_scores = factor_detail.get("factor_scores", {})

    print(f"\nStability score:      {metrics['stability_score']}/100"
          f"  [{factor_detail.get('score_band', '—')}]")
    print(f"Mean weekly income:   ₹{metrics['mean_weekly_income']:,.0f}")
    print(f"Income floor (P25):   ₹{factor_detail.get('factor_meta', {}).get('income_floor', {}).get('floor_value', '—')}")
    print(f"Robust CV:            {factor_detail.get('factor_meta', {}).get('regularity', {}).get('robust_cv', '—')}")

    if factor_scores:
        print("\nFactor scores:")
        weights = factor_detail.get("weights", {})
        for fname, fscore in factor_scores.items():
            w = weights.get(fname, 0)
            print(f"  {fname:<25} {fscore:>6.1f}  (weight {w:.0%})")

    print(f"\nExplanation:\n  {metrics['explanation']}")
    print(f"\nAction tip:\n  {metrics['action_tip']}")


if __name__ == "__main__":
    test_file("PhonePe CSV Export", CSV_PATH, is_csv=True)
    test_file("Bank of India PDF (clean)", BOI_PDF_PATH, is_csv=False)
    test_file("Bank of India PDF (TAMPERED)", TAMPERED_PDF_PATH, is_csv=False)