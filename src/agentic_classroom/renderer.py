"""
renderer.py — Markdown → PDF and interactive HTML conversion.

Dependencies (pure Python, no system libraries required):
    uv add xhtml2pdf markdown
"""

import re
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def convert_to_pdf(
    md_path: str,
    is_slides: bool = False,
    output_path: Optional[str] = None,
) -> Path:
    """Convert a Markdown file to a styled PDF using xhtml2pdf (cross-platform)."""
    try:
        import markdown as md_lib
    except ImportError as exc:
        raise ImportError("Required: uv add markdown") from exc
    try:
        from xhtml2pdf import pisa
    except ImportError as exc:
        raise ImportError("Required: uv add xhtml2pdf") from exc

    source = Path(md_path)
    if not source.exists():
        raise FileNotFoundError(f"Markdown file not found: {source}")
    dest = Path(output_path) if output_path else source.with_suffix(".pdf")

    raw = source.read_text(encoding="utf-8")
    raw = re.sub(r"^[ \t]+#", "#", raw, flags=re.MULTILINE)

    md_parser = md_lib.Markdown(
        extensions=["tables", "fenced_code", "codehilite", "nl2br", "sane_lists"]
    )

    content_html = (
        _render_slides(raw, md_parser) if is_slides else _render_document(raw, md_parser)
    )
    styled_html = _build_html(content_html, is_slides=is_slides)

    with open(str(dest), "wb") as f:
        status = pisa.CreatePDF(styled_html, dest=f)

    if status.err:
        raise RuntimeError(
            f"xhtml2pdf encountered {status.err} error(s) generating: {dest}"
        )

    print(f"PDF written to: {dest}")
    return dest


def generate_interactive_slides(md_path: str) -> Path:
    """Wrap Markdown in a Reveal.js HTML presentation."""
    source = Path(md_path)
    if not source.exists():
        raise FileNotFoundError(f"Markdown file not found: {source}")

    dest = source.parent / f"{source.stem}_interactive.html"
    dest.write_text(_build_revealjs(source.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"Interactive slides generated: {dest}")
    return dest


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _render_slides(raw: str, md_parser) -> str:
    """Split on --- separators and render each slide, pulling h1 into a header bar."""
    sections = [s.strip() for s in re.split(r"^---\s*$", raw, flags=re.MULTILINE)]
    sections = [s for s in sections if s]
    total = len(sections)
    blocks = []

    for i, section in enumerate(sections, start=1):
        h1_match = re.match(r"^#\s+(.+?)(?:\n|$)", section)
        if h1_match:
            title = h1_match.group(1).strip()
            body_md = section[h1_match.end():].strip()
            md_parser.reset()
            body_html = md_parser.convert(body_md) if body_md else ""
            slide = (
                f'<div class="slide">'
                f'<div class="slide-header"><h1>{title}</h1></div>'
                f'<div class="slide-body">{body_html}</div>'
                f'<div class="slide-footer">'
                f'<span class="slide-number">{i}&nbsp;/&nbsp;{total}</span>'
                f"</div></div>"
            )
        else:
            md_parser.reset()
            body_html = md_parser.convert(section)
            slide = (
                f'<div class="slide">'
                f'<div class="slide-body slide-body-plain">{body_html}</div>'
                f'<div class="slide-footer">'
                f'<span class="slide-number">{i}&nbsp;/&nbsp;{total}</span>'
                f"</div></div>"
            )
        blocks.append(slide)

    return "\n".join(blocks)


def _render_document(raw: str, md_parser) -> str:
    return f'<div class="page">{md_parser.convert(raw)}</div>'


# ─────────────────────────────────────────────
# HTML / CSS builders
# ─────────────────────────────────────────────

_SLIDE_CSS = """
@page {
    size: 297mm 167mm;
    margin: 0;
}

/* ── Slide container ── */
.slide {
    page-break-after: always;
    background-color: #ffffff;
    width: 297mm;
    overflow: hidden;
}
.slide:last-child { page-break-after: avoid; }

/* ── Title header bar ── */
.slide-header {
    background-color: #1e3a8a;
    padding: 22pt 44pt;
    border-bottom: 4pt solid #3b82f6;
}
.slide-header h1 {
    color: #ffffff;
    font-size: 28pt;
    font-weight: bold;
    margin: 0;
    line-height: 1.25;
    letter-spacing: -0.5pt;
}

/* ── Body ── */
.slide-body      { padding: 16pt 44pt 6pt 44pt; }
.slide-body-plain{ padding: 28pt 44pt 6pt 44pt; }

/* ── Footer / page number ── */
.slide-footer {
    padding: 5pt 44pt;
    border-top: 1pt solid #e2e8f0;
    margin-top: 8pt;
}
.slide-number {
    color: #94a3b8;
    font-size: 9pt;
    font-weight: bold;
    letter-spacing: 1pt;
}

/* ── Headings ── */
h2 {
    font-size: 20pt; color: #1e40af;
    margin: 0 0 10pt 0;
    border-bottom: 2pt solid #93c5fd;
    padding-bottom: 5pt;
}
h3 { font-size: 15pt; color: #2563eb; margin: 10pt 0 6pt 0; }
h4 { font-size: 13pt; color: #3b82f6; margin: 8pt 0 4pt 0; }

/* ── Body text ── */
p       { font-size: 15pt; color: #334155; line-height: 1.55; margin: 7pt 0; }
strong  { color: #1e3a8a; }
em      { color: #475569; }

/* ── Lists ── */
ul, ol  { margin: 7pt 0; padding-left: 28pt; }
li      { font-size: 15pt; color: #334155; line-height: 1.55; margin-bottom: 7pt; }

/* ── Code ── */
pre {
    background-color: #0f172a;
    color: #a7f3d0;
    padding: 12pt;
    font-size: 12pt;
    font-family: "Courier New", Courier, monospace;
    border-left: 5pt solid #10b981;
    margin: 10pt 0;
    white-space: pre-wrap;
}
code {
    font-family: "Courier New", Courier, monospace;
    font-size: 12pt;
    background-color: #f1f5f9;
    color: #be185d;
    padding: 2pt 5pt;
}
pre code { background-color: transparent; color: #a7f3d0; padding: 0; }

/* ── Blockquote ── */
blockquote {
    background-color: #eff6ff;
    border-left: 5pt solid #3b82f6;
    padding: 10pt 14pt;
    margin: 10pt 0;
    font-style: italic;
    color: #475569;
    font-size: 14pt;
}

/* ── Tables ── */
table               { border-collapse: collapse; width: 100%; margin: 10pt 0; font-size: 12pt; }
th                  { background-color: #1e40af; color: #ffffff; padding: 7pt 11pt; text-align: left; font-weight: bold; border: 1pt solid #1e3a8a; }
td                  { padding: 7pt 11pt; color: #334155; border: 1pt solid #e2e8f0; }
tr:nth-child(even) td { background-color: #f0f7ff; }

hr { border: none; border-top: 1pt solid #e2e8f0; margin: 12pt 0; }
"""

_DOCUMENT_CSS = """
@page {
    size: A4;
    margin: 22mm 18mm 22mm 18mm;
}

.page { padding: 0; }

/* ── Headings ── */
h1 {
    font-size: 22pt;
    color: #ffffff;
    background-color: #1e3a8a;
    padding: 14pt 18pt;
    margin: 0 0 18pt 0;
    border-bottom: 4pt solid #3b82f6;
    letter-spacing: -0.5pt;
}
h2 {
    font-size: 15pt; color: #1e40af;
    margin: 18pt 0 6pt 0;
    border-bottom: 1pt solid #bfdbfe;
    padding-bottom: 4pt;
}
h3 { font-size: 12pt; color: #2563eb; margin: 12pt 0 5pt 0; }
h4 { font-size: 11pt; color: #3b82f6; margin: 10pt 0 4pt 0; }

/* ── Body text ── */
p       { font-size: 11pt; color: #334155; line-height: 1.65; margin: 6pt 0; }
strong  { color: #1e3a8a; }
em      { color: #475569; }
a       { color: #2563eb; }

/* ── Lists ── */
ul, ol  { margin: 6pt 0; padding-left: 22pt; }
li      { font-size: 11pt; color: #334155; line-height: 1.6; margin: 3pt 0; }

/* ── Code ── */
pre {
    background-color: #0f172a;
    color: #4ade80;
    padding: 10pt;
    font-size: 9pt;
    font-family: "Courier New", Courier, monospace;
    border-left: 4pt solid #10b981;
    margin: 10pt 0;
    white-space: pre-wrap;
}
code {
    font-family: "Courier New", Courier, monospace;
    font-size: 9pt;
    background-color: #f1f5f9;
    color: #be185d;
    padding: 1pt 4pt;
}
pre code { background-color: transparent; color: #4ade80; padding: 0; }

/* ── Blockquote ── */
blockquote {
    background-color: #fefce8;
    border-left: 4pt solid #f59e0b;
    padding: 8pt 12pt;
    margin: 10pt 0;
    color: #78350f;
    font-style: italic;
    font-size: 10.5pt;
}

/* ── Tables ── */
table               { border-collapse: collapse; width: 100%; margin: 10pt 0; font-size: 10pt; }
th                  { background-color: #2563eb; color: #ffffff; padding: 6pt 10pt; text-align: left; font-weight: bold; border: 1pt solid #1e40af; }
td                  { padding: 6pt 10pt; color: #334155; border: 1pt solid #cbd5e1; }
tr:nth-child(even) td { background-color: #f8fafc; }

hr { border: none; border-top: 2pt solid #e2e8f0; margin: 14pt 0; }
"""


def _build_html(content_html: str, *, is_slides: bool) -> str:
    css = _SLIDE_CSS if is_slides else _DOCUMENT_CSS
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
* {{ margin: 0; padding: 0; }}
body {{
    font-family: Helvetica, Arial, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.6;
}}
{css}
</style>
</head>
<body>
{content_html}
</body>
</html>"""


def _build_revealjs(raw_md: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Presentation</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/reveal.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/theme/night.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/plugin/highlight/monokai.min.css">
    <style>
        .reveal h1, .reveal h2, .reveal h3 {{ color: #4ade80; text-transform: none; }}
        .reveal blockquote {{ background: rgba(255,255,255,0.05); border-left-color: #4ade80; }}
        .reveal pre {{ width: 100%; border-radius: 8px; }}
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
            controls: true, progress: true, center: true,
            hash: true, transition: 'slide',
            plugins: [ RevealMarkdown, RevealHighlight ]
        }});
    </script>
</body>
</html>"""
