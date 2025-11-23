# ---------------------------------------------------------
# This file defines a helper function for quality checking.
# We won't create a separate CrewAI Task here; instead, this
# helper can be used later if you want to extend the pipeline.
# For now, it's a simple placeholder used for documentation.
# ---------------------------------------------------------
def basic_quality_check(text: str) -> float:
    """
    Very simple heuristic quality check:
    - Longer than a minimal length?
    - Contains headings like 'Overview'?
    Returns a score between 0.0 and 1.0.
    """
    if not text or not text.strip():
        return 0.0

    score = 0.0
    if len(text.split()) > 50:
        score += 0.4
    if "Overview" in text or "Key Claims" in text:
        score += 0.3
    if "Sources" in text:
        score += 0.3

    return min(score, 1.0)
