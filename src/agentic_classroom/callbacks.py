"""
callbacks.py — Clean terminal status display for CrewAI execution.

task_done_callback : wired to Crew(task_callback=...), fires after every task
crew_starting      : call manually before crew.kickoff() to print a header
"""

import textwrap
from datetime import datetime

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_CYAN   = "\033[36m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_BLUE   = "\033[34m"
_PURPLE = "\033[35m"
_RED    = "\033[31m"

_ROLE_COLOURS = [_CYAN, _YELLOW, _PURPLE, _BLUE, _GREEN]
_colour_map: dict[str, str] = {}


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _role_colour(role: str) -> str:
    if role not in _colour_map:
        _colour_map[role] = _ROLE_COLOURS[len(_colour_map) % len(_ROLE_COLOURS)]
    return _colour_map[role]


def crew_starting(crew, model: str) -> None:
    """Print a header before a crew kicks off."""
    agents = ", ".join(a.role for a in crew.agents)
    tasks  = [t.description.strip().splitlines()[0][:60] for t in crew.tasks]

    print(f"\n{'─' * 64}")
    print(f"  {_BOLD}Crew starting{_RESET}  {_DIM}{_ts()}{_RESET}")
    print(f"  {_DIM}Model  :{_RESET} {_CYAN}{model}{_RESET}")
    print(f"  {_DIM}Agents :{_RESET} {agents}")
    for i, t in enumerate(tasks, 1):
        print(f"  {_DIM}Task {i}  :{_RESET} {t}...")
    print(f"{'─' * 64}")


def task_done_callback(output) -> None:
    """Fires when a task finishes. Receives a TaskOutput object."""
    agent   = getattr(output, "agent", "Agent")
    colour  = _role_colour(agent)
    raw     = getattr(output, "raw", "")
    summary = textwrap.shorten(raw.strip(), width=120, placeholder="...")

    print(f"\n  {_GREEN}{_BOLD}DONE{_RESET} {colour}{_BOLD}{agent}{_RESET} "
          f"{_DIM}finished at {_ts()}{_RESET}")
    print(f"  {_DIM}-> {summary}{_RESET}\n")
