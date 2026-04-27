from crewai import Task, Agent
from .client import create_llm
from textwrap import dedent


SLIDE_TEMPLATE = dedent("""\
    # {topic}
    *Course: AI Fundamentals*
    Presenter: Professor Dr. Raju

    ---

    # Objectives
    - <learning objective 1>
    - <learning objective 2>
    - <learning objective 3>
    - <learning objective 4>

    ---

    # Definition
    > <one-sentence authoritative definition of {topic}>
    - <key characteristic 1>
    - <key characteristic 2>

    ---

    # Core Concepts
    - **<concept 1>**: <one-line explanation>
    - **<concept 2>**: <one-line explanation>
    - **<concept 3>**: <one-line explanation>

    ---

    # How It Works
    - **Step 1 – <phase name>**: <what happens>
    - **Step 2 – <phase name>**: <what happens>
    - **Step 3 – <phase name>**: <what happens>

    ---

    # Code Example
```python
    # <brief comment describing what the snippet demonstrates>
    <self-contained, runnable Python code relevant to {topic}>
```

    ---

    # Use Cases
    - **<domain 1>**: <one-line description>
    - **<domain 2>**: <one-line description>
    - **<domain 3>**: <one-line description>

    ---

    # Comparison
    | Variant | Pros | Cons |
    |---------|------|------|
    | <variant 1> | <strength> | <weakness> |
    | <variant 2> | <strength> | <weakness> |
    | <variant 3> | <strength> | <weakness> |

    ---

    # Common Mistakes
    - **Mistake**: <mistake 1> → **Fix**: <how to avoid it>
    - **Mistake**: <mistake 2> → **Fix**: <how to avoid it>

    ---

    # Summary
    - <key takeaway 1>
    - <key takeaway 2>
    - <key takeaway 3>

    ---

    # Questions?
""")


SLIDE_RULES = dedent("""\
    OUTPUT RULES — follow exactly, no exceptions:
    1. Output ONLY the slide content — no preamble, no sign-off, no commentary.
    2. Separate every slide with a line containing exactly three dashes: ---
    3. Every slide title must be a single `#` heading; no `##` or deeper for titles.
    4. Replace every <placeholder> with real, topic-specific content.
    5. Keep each slide focused: 3–5 bullet points or one short code block max.
    6. The code slide must contain a complete, runnable Python snippet (not pseudocode).
    7. Do not number the slide titles (e.g. "Slide 1:", "Slide 2:") — titles only.
    8. Do not use any emojis anywhere in the output.
""")


def create_slides_task(agent: Agent, topic: str) -> Task:
    template = SLIDE_TEMPLATE.replace("{topic}", topic)

    description = dedent(f"""\
        Create an 11-slide educational presentation on: **{topic}**

        {SLIDE_RULES}

        Fill in the template below, replacing every <placeholder> with
        accurate, topic-specific content about {topic}:

        {template}

        Once you have completed writing all the slides, call the
        create_presentation tool with the topic and the full slides markdown
        to generate the PDF and HTML files.
    """)

    expected_output = dedent("""\
        Exactly 11 slides of well-structured Markdown, where:
        - Each slide is separated by a lone `---` on its own line
        - Every slide opens with a single `#` heading (no slide numbers in the title)
        - All <placeholder> tokens have been replaced with real content
        - The code slide contains a complete, runnable Python snippet
        - No text appears before slide 1 or after slide 11
        - The create_presentation tool was called to generate the PDF and HTML files
    """)

    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
    )


def create_quiz_task(agent: Agent, topic: str, slides_content: str) -> Task:
    return Task(
        description=(
            f"Create a quiz with explanations for the topic: '{topic}'.\n\n"
            "Based on the following lecture slides:\n\n"
            f"{slides_content}\n\n"
            "Create:\n"
            "- 5 multiple choice questions testing key concepts\n"
            "- 3 short answer questions for deeper understanding\n"
            "- Detailed explanations for each answer\n"
            "- Reference to relevant slide numbers\n\n"
            "Format: Clear markdown with questions, options, and detailed explanations. Do not use any emojis."
        ),
        agent=agent,
        expected_output="A comprehensive quiz with multiple choice and short answer questions, each with detailed explanations",
    )


def create_questions_task(
    agent: Agent, topic: str, slides_content: str, quiz_content: str
) -> Task:
    return Task(
        description=(
            f"Generate potential questions a student might ask about: '{topic}'.\n\n"
            "Based on the lecture slides:\n\n"
            f"{slides_content}\n\n"
            "And the quiz:\n\n"
            f"{quiz_content}\n\n"
            "Generate:\n"
            "- 5-7 clarification questions (seeking more explanation)\n"
            "- 3-5 application questions (how to apply concepts)\n"
            "- 2-3 edge case questions (corner cases or exceptions)\n\n"
            "Format: Organized by category with brief context for each question. Do not use any emojis."
        ),
        agent=agent,
        expected_output="A list of thoughtful questions organized by type (clarification, application, edge cases)",
    )


def create_answers_task(
    agent: Agent, topic: str, slides_content: str, questions_content: str
) -> Task:
    return Task(
        description=(
            f"Answer the questions generated by the student about: '{topic}'.\n\n"
            "Based on the following lecture slides:\n\n"
            f"{slides_content}\n\n"
            "Here are the student's questions:\n\n"
            f"{questions_content}\n\n"
            "Provide:\n"
            "- A detailed, encouraging, and clear answer for each question\n"
            "- Code examples where appropriate to clarify points\n"
            "- References to specific slide concepts if applicable\n\n"
            "Format: Use clear markdown with headers for each question and its detailed answer. Do not use any emojis."
        ),
        agent=agent,
        expected_output="Detailed, accurate, and encouraging answers to all the student's questions, formatted in markdown.",
    )
