import os
import logging
from crewai import Crew

from .agents import create_professor_agent, create_ta_agent, create_student_agent
from .tasks import (
    create_slides_task,
    create_quiz_task,
    create_questions_task,
    create_answers_task,
)
from .renderer import convert_to_pdf, generate_interactive_slides
from .visualization import save_crew_view
from .client import kickoff_with_fallback
from .callbacks import task_done_callback

# Suppress CrewAI's repeated OpenTelemetry initialisation warnings
logging.getLogger("opentelemetry").setLevel(logging.ERROR)

TOPIC = "API in python"
OUTPUT_DIR = "output"

_CREW_OPTS = dict(verbose=False, task_callback=task_done_callback)


def sanitize_filename(name: str) -> str:
    return (
        "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name)
        .strip()
        .replace(" ", "_")
    )


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    topic_safe = sanitize_filename(TOPIC)

    print(f"\n=== Agentic Classroom ===")
    print(f"Topic: {TOPIC}")
    print(f"Starting workflow...\n")

    professor = create_professor_agent()
    ta        = create_ta_agent()
    student   = create_student_agent()

    # ── Visualization-only crew (not executed) ───────────────────────────────
    full_crew = Crew(
        agents=[professor, ta, student],
        tasks=[
            create_slides_task(professor, TOPIC),
            create_quiz_task(ta, TOPIC, "{slides_content}"),
            create_questions_task(student, TOPIC, "{slides_content}", "{quiz_content}"),
            create_answers_task(ta, TOPIC, "{slides_content}", "{questions_content}"),
        ],
        verbose=False,
    )
    save_crew_view(full_crew, f"{OUTPUT_DIR}/{topic_safe}_full_crew_visualization.html")

    # ── Step 1: Slides ───────────────────────────────────────────────────────
    print("--- Step 1: Professor creates slides ---")
    crew1 = Crew(
        agents=[professor],
        tasks=[create_slides_task(professor, TOPIC)],
        **_CREW_OPTS,
    )
    save_crew_view(crew1, f"{OUTPUT_DIR}/{topic_safe}_crew1_visualization.html")

    slides_content = str(kickoff_with_fallback(crew1))
    slides_file = f"{OUTPUT_DIR}/{topic_safe}_slides.md"
    _write(slides_file, slides_content)
    generate_interactive_slides(slides_file)
    convert_to_pdf(slides_file, is_slides=True)

    # ── Step 2: Quiz ─────────────────────────────────────────────────────────
    print("\n--- Step 2: TA creates quiz ---")
    crew2 = Crew(
        agents=[ta],
        tasks=[create_quiz_task(ta, TOPIC, slides_content)],
        **_CREW_OPTS,
    )
    save_crew_view(crew2, f"{OUTPUT_DIR}/{topic_safe}_crew2_visualization.html")

    quiz_content = str(kickoff_with_fallback(crew2))
    quiz_file = f"{OUTPUT_DIR}/{topic_safe}_quiz.md"
    _write(quiz_file, f"# Quiz: {TOPIC}\n\n{quiz_content}")
    convert_to_pdf(quiz_file)

    # ── Step 3: Student questions ─────────────────────────────────────────────
    print("\n--- Step 3: Student generates questions ---")
    crew3 = Crew(
        agents=[student],
        tasks=[create_questions_task(student, TOPIC, slides_content, quiz_content)],
        **_CREW_OPTS,
    )
    save_crew_view(crew3, f"{OUTPUT_DIR}/{topic_safe}_crew3_visualization.html")

    questions_content = str(kickoff_with_fallback(crew3))
    questions_file = f"{OUTPUT_DIR}/{topic_safe}_questions.md"
    _write(questions_file, f"# Student Questions: {TOPIC}\n\n{questions_content}")
    convert_to_pdf(questions_file)

    # ── Step 4: TA answers ────────────────────────────────────────────────────
    print("\n--- Step 4: TA answers questions ---")
    crew4 = Crew(
        agents=[ta],
        tasks=[create_answers_task(ta, TOPIC, slides_content, questions_content)],
        **_CREW_OPTS,
    )
    answers_content = str(kickoff_with_fallback(crew4))
    answers_file = f"{OUTPUT_DIR}/{topic_safe}_answers.md"
    _write(answers_file, f"# TA Answers: {TOPIC}\n\n{answers_content}")
    convert_to_pdf(answers_file)

    print("\n=== Workflow Complete ===")
    for f in [slides_file, quiz_file, questions_file, answers_file]:
        print(f"  - {f}")


def _write(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)
    print(f"  Saved: {path}")


if __name__ == "__main__":
    main()
