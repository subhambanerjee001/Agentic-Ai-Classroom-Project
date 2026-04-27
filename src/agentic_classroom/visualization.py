"""
visualization.py — Crew visualization helpers.

Wraps ai_trace.save_view to display concise task summaries
instead of full prompts in the flow diagram.
"""

from ai_trace.trace_crewai import save_view as _save_view

_DESC_LIMIT = 120
_OUTPUT_LIMIT = 80


def save_crew_view(crew, path: str) -> None:
    """Save a crew flow diagram with truncated task text for readability."""
    _originals = _snapshot(crew)
    _apply_truncated(crew)
    try:
        _save_view(crew, path)
    finally:
        _restore(crew, _originals)
    print(f"Crew visualization saved to: {path}")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _snapshot(crew) -> dict:
    return {
        str(task.id): (task.description, task.expected_output)
        for task in crew.tasks
    }


def _apply_truncated(crew) -> None:
    for task in crew.tasks:
        task.description = _truncate(task.description, _DESC_LIMIT)
        task.expected_output = _truncate(task.expected_output, _OUTPUT_LIMIT)


def _restore(crew, originals: dict) -> None:
    for task in crew.tasks:
        task.description, task.expected_output = originals[str(task.id)]


def _truncate(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    # Break at the last word boundary within the limit
    cut = text.rfind(" ", 0, limit)
    return text[: cut if cut > 0 else limit] + "…"
