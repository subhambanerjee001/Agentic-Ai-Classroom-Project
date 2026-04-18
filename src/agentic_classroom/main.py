import os
from crewai import Crew
from md2pdf import md2pdf

from .agents import create_professor_agent, create_ta_agent, create_student_agent
from .tasks import (
    create_slides_task,
    create_quiz_task,
    create_questions_task,
    create_answers_task,
)
from ai_trace.trace_crewai import save_view


TOPIC = "Temperature in LLMs"
OUTPUT_DIR = "output"


def sanitize_filename(name: str) -> str:
    return (
        "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name)
        .strip()
        .replace(" ", "_")
    )


from pathlib import Path
from typing import Optional
import re


def convert_to_pdf(
    md_path: str,
    is_slides: bool = False,
    output_path: Optional[str] = None,
) -> Path:
    try:
        import markdown as md_lib
    except ImportError as exc:
        raise ImportError(
            "The 'markdown' package is required: pip install markdown"
        ) from exc

    try:
        from weasyprint import HTML as WeasyprintHTML
    except ImportError as exc:
        raise ImportError(
            "The 'weasyprint' package is required: pip install weasyprint"
        ) from exc

    source = Path(md_path)
    if not source.exists():
        raise FileNotFoundError(f"Markdown file not found: {source}")

    dest = Path(output_path) if output_path else source.with_suffix(".pdf")

    raw = source.read_text(encoding="utf-8")

    # Clean up leading spaces before markdown headers which break formatting
    raw = re.sub(r"^[ \t]+#", "#", raw, flags=re.MULTILINE)

    md_parser = md_lib.Markdown(
        extensions=["tables", "fenced_code", "codehilite", "nl2br", "sane_lists"]
    )

    if is_slides:
        sections = [s.strip() for s in re.split(r"^---\s*$", raw, flags=re.MULTILINE)]
        sections = [s for s in sections if s]
        total = len(sections)
        html_blocks = []
        for i, section in enumerate(sections, start=1):
            md_parser.reset()
            body = md_parser.convert(section)
            html_blocks.append(
                f'<div class="slide">'
                f"{body}"
                f'<div class="slide-number">{i} / {total}</div>'
                f"</div>"
            )
        content_html = "\n".join(html_blocks)
    else:
        content_html = f'<div class="page">{md_parser.convert(raw)}</div>'

    styled_html = _build_html(content_html, is_slides=is_slides)

    try:
        WeasyprintHTML(string=styled_html, base_url=str(source.parent)).write_pdf(
            str(dest)
        )
    except Exception as exc:
        raise RuntimeError(f"WeasyPrint failed to generate PDF: {exc}") from exc

    print(f"PDF written to: {dest}")
    return dest


def _build_html(content_html: str, *, is_slides: bool) -> str:
    if is_slides:
        slide_specific_css = """
        .slide {
            page-break-after: always;
            height: 100vh;
            padding: 40pt 60pt;
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            background: #ffffff;
        }
        .slide:last-child { page-break-after: avoid; }
        .slide-number {
            position: absolute;
            bottom: 24pt;
            right: 40pt;
            font-size: 14pt;
            color: #94a3b8;
            font-weight: 600;
        }
        h1 {
            font-size: 42pt;
            color: #ffffff;
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
            padding: 30pt 60pt;
            margin: -40pt -60pt 40pt -60pt;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        h2 { font-size: 32pt; color: #1e40af; margin: 0 0 20pt 0; font-weight: 600; border-bottom: 3px solid #bfdbfe; padding-bottom: 10pt; display: inline-block;}
        h3 { font-size: 26pt; color: #3b82f6; margin: 15pt 0; }
        p, ul, ol, li { font-size: 22pt; color: #334155; line-height: 1.6; }
        p { margin: 12pt 0; }
        ul, ol { margin: 12pt 0; padding-left: 40pt; }
        li { margin-bottom: 16pt; }
        pre {
            background: #1e293b; color: #a7f3d0; padding: 20pt; font-size: 18pt;
            border-radius: 8pt; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
            border-left: 6px solid #10b981; margin: 20pt 0;
            overflow-x: auto; white-space: pre-wrap;
        }
        code { font-size: 18pt; background: #f1f5f9; color: #be185d; padding: 4pt 10pt; border-radius: 6pt; }
        pre code { background: none; color: inherit; padding: 0; }
        blockquote {
            background: #f8fafc; border-left: 8pt solid #3b82f6;
            padding: 15pt 24pt; font-size: 24pt; font-style: italic; color: #475569;
            margin: 20pt 0; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
            border-radius: 0 8pt 8pt 0;
        }
        table { font-size: 18pt; margin: 20pt 0; }
        th, td { padding: 16pt 20pt; }
        """
    else:
        slide_specific_css = """
        .page { padding: 0; }
        h1 { font-size: 24pt; color: #1e3a5f; border-bottom: 2px solid #2563eb; padding-bottom: 6pt; }
        h2 { font-size: 18pt; color: #1e40af; margin-top: 18pt; }
        h3 { font-size: 14pt; color: #374151; }
        p, ul, ol, li { font-size: 11pt; color: #334155; line-height: 1.6; }
        p  { margin: 7pt 0; }
        ul, ol { margin: 7pt 0; padding-left: 22pt; }
        li { margin: 4pt 0; }
        pre {
            background: #1e293b; color: #4ade80; padding: 12pt; font-size: 9.5pt;
            border-radius: 4pt; overflow-x: auto; white-space: pre-wrap; margin: 10pt 0;
        }
        code { background: #f1f5f9; color: #be185d; padding: 2pt 4pt; border-radius: 3pt; font-size: 9.5pt; }
        pre code { background: none; color: inherit; padding: 0; }
        blockquote {
            background: #fef9c3; border-left: 4pt solid #f59e0b;
            padding: 10pt 14pt; margin: 10pt 0; color: #78350f;
        }
        table { font-size: 10pt; margin: 10pt 0; }
        th, td { padding: 7pt 10pt; }
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
@page {{
    size: {"16in 9in" if is_slides else "A4"};
    margin: {"0.4in" if is_slides else "0.75in"};
}}
body {{
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    line-height: 1.6;
}}
{slide_specific_css}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #cbd5e1; }}
th {{ background: #2563eb; color: white; font-weight: 600; text-align: left; }}
tr:nth-child(even) {{ background: #f8fafc; }}
a {{ color: #2563eb; text-decoration: none; }}
img {{ max-width: 100%; border-radius: 8pt; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin: 15pt 0; }}
</style>
</head>
<body>
{content_html}
</body>
</html>"""


def generate_interactive_slides(md_path: str) -> Path:
    source = Path(md_path)
    if not source.exists():
        raise FileNotFoundError(f"Markdown file not found: {source}")

    # Output to _presentation.html to distinguish it
    dest = source.parent / f"{source.stem}_interactive.html"
    raw_md = source.read_text(encoding="utf-8")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Presentation</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/reveal.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/theme/night.min.css" id="theme">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/plugin/highlight/monokai.min.css">
    <style>
        .reveal h1, .reveal h2, .reveal h3 {{
            color: #4ade80; /* Soft green accents to look professional with night theme */
            text-transform: none; /* Keep original casing */
        }}
        .reveal blockquote {{ background: rgba(255,255,255,0.05); border-left-color: #4ade80; }}
        .reveal pre {{ width: 100%; box-shadow: 0 5px 15px rgba(0,0,0,0.5); border-radius: 8px; }}
        .reveal .slides section {{ padding: 20px; }}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
            <section data-markdown data-separator="^---\\s*$" data-separator-vertical="^___\\s*$">
                <textarea data-template>
{raw_md}
                </textarea>
            </section>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/reveal.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/plugin/markdown/markdown.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/plugin/highlight/highlight.js"></script>
    <script>
        Reveal.initialize({{
            controls: true,
            progress: true,
            center: true,
            hash: true,
            transition: 'slide',
            plugins: [ RevealMarkdown, RevealHighlight ]
        }});
    </script>
</body>
</html>"""

    dest.write_text(html_content, encoding="utf-8")
    print(f"Interactive slides generated: {dest}")
    return dest


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    topic_safe = sanitize_filename(TOPIC)

    print(f"\n=== Agentic Classroom ===")
    print(f"Topic: {TOPIC}")
    print(f"Starting workflow...\n")

    professor = create_professor_agent()
    ta = create_ta_agent()
    student = create_student_agent()

    print("--- Full Agent Workflow Visualization ---")
    slides_task = create_slides_task(professor, TOPIC)
    quiz_task = create_quiz_task(ta, TOPIC, "{slides_content}")
    questions_task = create_questions_task(
        student, TOPIC, "{slides_content}", "{quiz_content}"
    )
    answers_task = create_answers_task(
        ta, TOPIC, "{slides_content}", "{questions_content}"
    )

    full_crew = Crew(
        agents=[professor, ta, student],
        tasks=[slides_task, quiz_task, questions_task, answers_task],
        verbose=True,
    )

    save_view(full_crew, f"output/{topic_safe}_full_crew_visualization.html")
    print(
        f"Full crew visualization saved to: output/{topic_safe}_full_crew_visualization.html"
    )
    print()

    print("--- Step 1: Professor creates slides ---")
    slides_task = create_slides_task(professor, TOPIC)
    crew1 = Crew(agents=[professor], tasks=[slides_task], verbose=True)

    save_view(crew1, f"output/{topic_safe}_crew1_visualization.html")
    print(f"Crew visualization saved to: output/{topic_safe}_crew1_visualization.html")

    slides_result = crew1.kickoff()
    slides_content = str(slides_result)

    slides_file = os.path.join(OUTPUT_DIR, f"{topic_safe}_slides.md")
    with open(slides_file, "w") as f:
        f.write(slides_content)
    print(f"Slides saved to: {slides_file}")

    html_result = generate_interactive_slides(slides_file)
    print(f"Interactive HTML result: {html_result}")

    pdf_result = convert_to_pdf(slides_file, is_slides=True)
    print(f"PDF result: {pdf_result}")
    print()

    print("--- Step 2: TA creates quiz and explanations ---")
    quiz_task = create_quiz_task(ta, TOPIC, slides_content)
    crew2 = Crew(agents=[ta], tasks=[quiz_task], verbose=True)

    save_view(crew2, f"output/{topic_safe}_crew2_visualization.html")
    print(f"Crew visualization saved to: output/{topic_safe}_crew2_visualization.html")

    quiz_result = crew2.kickoff()
    quiz_content = str(quiz_result)

    quiz_file = os.path.join(OUTPUT_DIR, f"{topic_safe}_quiz.md")
    with open(quiz_file, "w") as f:
        f.write(f"# Quiz: {TOPIC}\n\n")
        f.write(quiz_content)
    print(f"Quiz saved to: {quiz_file}")
    convert_to_pdf(quiz_file)
    print()

    print("--- Step 3: Student generates questions ---")
    questions_task = create_questions_task(student, TOPIC, slides_content, quiz_content)
    crew3 = Crew(agents=[student], tasks=[questions_task], verbose=True)

    save_view(crew3, f"output/{topic_safe}_crew3_visualization.html")
    print(f"Crew visualization saved to: output/{topic_safe}_crew3_visualization.html")

    questions_result = crew3.kickoff()
    questions_content = str(questions_result)

    questions_file = os.path.join(OUTPUT_DIR, f"{topic_safe}_questions.md")
    with open(questions_file, "w") as f:
        f.write(f"# Student Questions: {TOPIC}\n\n")
        f.write(questions_content)
    print(f"Questions saved to: {questions_file}")
    convert_to_pdf(questions_file)
    print()

    print("--- Step 4: TA answers questions ---")
    answers_task = create_answers_task(ta, TOPIC, slides_content, questions_content)
    crew4 = Crew(agents=[ta], tasks=[answers_task], verbose=True)
    answers_result = crew4.kickoff()
    answers_content = str(answers_result)

    answers_file = os.path.join(OUTPUT_DIR, f"{topic_safe}_answers.md")
    with open(answers_file, "w") as f:
        f.write(f"# TA Answers: {TOPIC}\n\n")
        f.write(answers_content)
    print(f"Answers saved to: {answers_file}")
    convert_to_pdf(answers_file)
    print()

    print("=== Workflow Complete ===")
    print(f"Output files:")
    print(f"  - {slides_file}")
    print(f"  - {quiz_file}")
    print(f"  - {questions_file}")
    print(f"  - {answers_file}")


if __name__ == "__main__":
    main()
