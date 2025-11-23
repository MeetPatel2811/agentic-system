# ---------------------------------------------------------
# This file defines the custom Claim–Evidence Extractor tool.
# - This is your CUSTOM tool for the assignment.
# - It uses simple rules to split sentences into "claims" and "evidence".
# - The Analysis Agent calls this to structure its findings.
# ---------------------------------------------------------
from crewai.tools import tool

ASSERTIVE_HINTS = [
    "is", "are", "shows", "demonstrates", "indicates",
    "suggests", "enables", "improves", "allows", "can",
]


def _extract_claims_and_evidence(text: str, max_items: int = 5):
    """
    Very simple heuristic extractor:
    - Sentences containing assertive words are treated as claims.
    - Others are treated as potential evidence.
    """
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    claims, evidence = [], []

    for s in sentences:
        lowered = s.lower()
        if any(h in lowered for h in ASSERTIVE_HINTS):
            claims.append(s)
        else:
            evidence.append(s)
        if len(claims) >= max_items and len(evidence) >= max_items:
            break

    return claims[:max_items], evidence[:max_items]


@tool("Claim–Evidence Extractor")
def claim_extractor_tool(text: str) -> str:
    """
    Extract up to 5 claims and 5 evidence sentences from text.
    Returns a structured plain-text format with 'Claims:' and 'Evidence:' sections.
    """
    if not text or not text.strip():
        return "Claims: []\nEvidence: []"

    claims, evidence = _extract_claims_and_evidence(text, max_items=5)
    lines = ["Claims:"]
    for i, c in enumerate(claims, 1):
        lines.append(f"{i}. {c}")
    lines.append("Evidence:")
    for i, e in enumerate(evidence, 1):
        lines.append(f"{i}. {e}")
    return "\n".join(lines)
