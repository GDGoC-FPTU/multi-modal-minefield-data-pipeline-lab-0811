"""Quality Check Module: Validate documents against semantic quality gates.

Implements multi-layer validation to detect and reject:
- Corrupt or incomplete data (missing content)
- Toxic/error keywords that indicate extraction failures
- Logic discrepancies (comment % vs code % mismatch)

Author: Observability & QA Engineer (Role 3)
"""

# ==========================================
# ROLE 3: OBSERVABILITY & QA ENGINEER
# ==========================================
# Task: Implement quality gates to reject corrupt data or logic discrepancies.
import re
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def run_quality_gate(document_dict: Dict[str, Any]) -> bool:
    """Run quality gates on a document.

    Quality Gates (sequentially applied):
    1. CONTENT_LENGTH: Reject if `content` missing or < 20 characters
    2. TOXIC_KEYWORDS: Reject if `content` contains error/failure markers
    3. PERCENT_DISCREPANCY: Reject if comment % != code %

    Returns:
        bool: True if document passes all gates, False if any gate rejects it.
        
    Logs warnings for failed gates with document ID for tracing.
    """
    doc_id = document_dict.get("document_id", "<unknown>")
    
    # GATE 1: Content length validation
    content = document_dict.get("content", "")
    if not isinstance(content, str):
        logger.warning(f"[GATE 1] {doc_id}: content is not a string (type={type(content).__name__})")
        return False
    
    content_clean = content.strip()
    if len(content_clean) < 20:
        logger.warning(f"[GATE 1] {doc_id}: content too short ({len(content_clean)} chars, min 20)")
        return False
    
    logger.debug(f"[GATE 1] {doc_id}: PASSED (content length={len(content_clean)})")

    # GATE 2: Toxic keyword check (case-insensitive)
    # Expanded list of error keywords that indicate extraction failures
    toxic_keywords = [
        "null pointer exception",
        "ocr error",
        "traceback",
        "critical error",
        "failed to",
        "error:",
        "exception:",
        "invalid format",
        "parsing failed",
        "corrupt"
    ]
    content_lower = content_clean.lower()
    toxic_found = []
    for kw in toxic_keywords:
        if kw in content_lower:
            toxic_found.append(kw)
    
    if toxic_found:
        logger.warning(f"[GATE 2] {doc_id}: toxic keywords detected: {toxic_found}")
        return False
    
    logger.debug(f"[GATE 2] {doc_id}: PASSED (no toxic keywords)")

    # Helper: extract first percent number from a string (e.g., '8%' -> 8.0)
    def extract_percent(s: Any):
        """Extract first percentage value from string (e.g., '8%' → 8.0)"""
        if not isinstance(s, str):
            return None
        m = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
        return float(m.group(1)) if m else None

    # GATE 3: Percent discrepancy check
    # Field-level discrepancy: look for explicit keys that may hold comment/code percentages
    tax_comment_pct = extract_percent(document_dict.get("tax_comment") or document_dict.get("comment") or document_dict.get("note"))
    tax_code_pct = extract_percent(document_dict.get("tax_code") or document_dict.get("code") or document_dict.get("calculation") or document_dict.get("calc"))

    if tax_comment_pct is not None and tax_code_pct is not None:
        if abs(tax_comment_pct - tax_code_pct) > 1e-6:
            logger.warning(f"[GATE 3] {doc_id}: field-level % discrepancy (comment={tax_comment_pct}%, code={tax_code_pct}%)")
            return False

    # Content-level heuristic: detect explicit 'comment ... X% ... code ... Y%' patterns
    m = re.search(r"comment[^%\d]{0,60}?(\d+(?:\.\d+)?)\s*%.*?code[^%\d]{0,60}?(\d+(?:\.\d+)?)\s*%", content_clean, flags=re.I | re.S)
    if not m:
        m = re.search(r"code[^%\d]{0,60}?(\d+(?:\.\d+)?)\s*%.*?comment[^%\d]{0,60}?(\d+(?:\.\d+)?)\s*%", content_clean, flags=re.I | re.S)
    if m:
        a = float(m.group(1))
        b = float(m.group(2))
        if abs(a - b) > 1e-6:
            logger.warning(f"[GATE 3] {doc_id}: content-level % discrepancy (val1={a}%, val2={b}%)")
            return False
    
    logger.debug(f"[GATE 3] {doc_id}: PASSED (no % discrepancies)")
    return True
