# ==========================================
# ROLE 3: OBSERVABILITY & QA ENGINEER
# ==========================================
# Task: Implement quality gates to reject corrupt data or logic discrepancies.
import re
from typing import Any, Dict

def run_quality_gate(document_dict: Dict[str, Any]) -> bool:
    """Run quality gates on a document.

    Gates:
    - Reject if `content` missing or shorter than 20 characters.
    - Reject if `content` contains toxic/error keywords.
    - Reject if a clear percentage discrepancy is detected between comment/code.

    Returns True if the document passes all gates, False otherwise.
    """
    content = document_dict.get("content", "")
    if not isinstance(content, str) or len(content.strip()) < 20:
        return False

    # Toxic keyword check (case-insensitive)
    toxic_keywords = ["Null pointer exception", "OCR Error", "Traceback", "Critical Error"]
    content_lower = content.lower()
    for kw in toxic_keywords:
        if kw.lower() in content_lower:
            return False

    # Helper: extract first percent number from a string (e.g., '8%' -> 8.0)
    def extract_percent(s: Any):
        if not isinstance(s, str):
            return None
        m = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
        return float(m.group(1)) if m else None

    # Field-level discrepancy: look for explicit keys that may hold comment/code percentages
    tax_comment_pct = extract_percent(document_dict.get("tax_comment") or document_dict.get("comment") or document_dict.get("note"))
    tax_code_pct = extract_percent(document_dict.get("tax_code") or document_dict.get("code") or document_dict.get("calculation") or document_dict.get("calc"))

    if tax_comment_pct is not None and tax_code_pct is not None:
        if abs(tax_comment_pct - tax_code_pct) > 1e-6:
            return False

    # Content-level heuristic: detect explicit 'comment ... X% ... code ... Y%' patterns
    m = re.search(r"comment[^%\d]{0,60}?(\d+(?:\.\d+)?)\s*%.*?code[^%\d]{0,60}?(\d+(?:\.\d+)?)\s*%", content, flags=re.I | re.S)
    if not m:
        m = re.search(r"code[^%\d]{0,60}?(\d+(?:\.\d+)?)\s*%.*?comment[^%\d]{0,60}?(\d+(?:\.\d+)?)\s*%", content, flags=re.I | re.S)
    if m:
        a = float(m.group(1))
        b = float(m.group(2))
        if abs(a - b) > 1e-6:
            return False

    return True
