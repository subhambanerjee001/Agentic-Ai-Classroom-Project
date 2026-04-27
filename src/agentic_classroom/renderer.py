"""
renderer.py — Markdown → PDF and interactive HTML conversion.

Dependencies (pure Python, no system libraries required):
    uv add xhtml2pdf markdown
"""

import re
from pathlib import Path
from typing import Optional


# ── Unicode → ASCII sanitisation ─────────────────────────────────────────────
# xhtml2pdf uses built-in Helvetica/Arial which have no glyphs for these
# characters, rendering them as black squares.  Replace before conversion.
_UNICODE_MAP = str.maketrans({
    "\u2014": "--",    # em dash —
    "\u2013": "-",     # en dash –
    "\u2012": "-",     # figure dash ‒
    "\u2011": "-",     # non-breaking hyphen ‑
    "\u2010": "-",     # hyphen ‐
    "\u201c": '"',     # left double quote "
    "\u201d": '"',     # right double quote "
    "\u2018": "'",     # left single quote '
    "\u2019": "'",     # right single quote '
    "\u2026": "...",   # ellipsis …
    "\u00a0": " ",     # non-breaking space
    "\u00b7": "-",     # middle dot ·
    "\u2022": "-",     # bullet •  (markdown renders its own bullets)
    "\u2192": "->",    # right arrow →
    "\u2190": "<-",    # left arrow ←
    "\u00ab": "<<",    # left guillemet «
    "\u00bb": ">>",    # right guillemet »
    "\u00e9": "e",     # é
    "\u00e8": "e",     # è
    "\u00ea": "e",     # ê
    "\u00e0": "a",     # à
    "\u00e2": "a",     # â
    "\u00f4": "o",     # ô
    "\u00fb": "u",     # û
    "\u00fc": "u",     # ü
    "\u00e4": "a",     # ä
    "\u00f6": "o",     # ö
})


def _sanitize(text: str) -> str:
    """Replace Unicode characters that xhtml2pdf cannot render."""
    return text.translate(_UNICODE_MAP)


# ── Page geometry (167mm × 297mm landscape) ──────────────────────────────────
# 1 mm ≈ 2.835 pt  →  167mm ≈ 473 pt  (page height)
_HEADER_H  = "64pt"   # title bar
_BODY_H    = "379pt"  # content area  (473 - 64 - 30 = 379)
_FOOTER_H  = "30pt"   # page-number strip
_TITLE_H   = "443pt"  # title-slide body (no header bar: 473 - 30)


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
    raw = _sanitize(raw)
    raw = re.sub(r"^[ \t]+#", "#", raw, flags=re.MULTILINE)

    # NOTE: nl2br converts \n→<br> inside code blocks (breaks indentation).
    # codehilite generates Pygments spans that xhtml2pdf cannot render.
    # Use only basic extensions for reliable PDF output.
    md_parser = md_lib.Markdown(
        extensions=["tables", "fenced_code", "sane_lists"]
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

    print(f"  PDF written to: {dest}")
    return dest


def generate_interactive_slides(md_path: str) -> Path:
    """Wrap Markdown in a Reveal.js HTML presentation."""
    source = Path(md_path)
    if not source.exists():
        raise FileNotFoundError(f"Markdown file not found: {source}")

    dest = source.parent / f"{source.stem}_interactive.html"
    dest.write_text(_build_revealjs(source.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"  Interactive slides generated: {dest}")
    return dest


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _fix_pre_whitespace(html: str) -> str:
    """
    xhtml2pdf does not honour white-space:pre, and applies inline <code>
    background styling to every text run inside <pre><code>...</code></pre>,
    causing white highlight boxes on each line.

    This function:
      1. Strips the inner <code ...> wrapper added by fenced_code
      2. Converts newlines → <br/>
      3. Replaces leading spaces with &nbsp; to preserve indentation
    """
    def _rewrite(m: re.Match) -> str:
        inner = m.group(1).strip()
        # Remove the <code class="..."> wrapper fenced_code adds
        inner = re.sub(r"^<code[^>]*>", "", inner)
        inner = re.sub(r"</code>$", "", inner.strip())
        lines = inner.split("\n")
        out = []
        for line in lines:
            n = len(line) - len(line.lstrip(" "))
            out.append("&nbsp;" * n + line[n:])
        return "<pre>" + "<br/>".join(out) + "</pre>"

    return re.sub(r"<pre>(.*?)</pre>", _rewrite, html, flags=re.DOTALL)


def _render_slides(raw: str, md_parser) -> str:
    """
    Render each slide as a fixed-height table so the footer is always
    pinned to the bottom of the page regardless of content length.
    """
    sections = [s.strip() for s in re.split(r"^---\s*$", raw, flags=re.MULTILINE)]
    sections = [s for s in sections if s]
    total = len(sections)
    blocks = []

    for i, section in enumerate(sections, start=1):
        h1_match = re.match(r"^#\s+(.+?)(?:\n|$)", section)
        title    = h1_match.group(1).strip() if h1_match else ""
        body_md  = section[h1_match.end():].strip() if h1_match else section

        md_parser.reset()
        body_html = md_parser.convert(body_md) if body_md else ""
        body_html = _fix_pre_whitespace(body_html)
        # Scope any markdown-generated tables so they don't inherit layout styles
        body_html = body_html.replace("<table>", '<table class="data-table" width="100%">')

        footer = (
            f'<tr><td class="slide-footer">'
            f'<span class="slide-num">{i}&nbsp;/&nbsp;{total}</span>'
            f'</td></tr>'
        )

        # Slides containing a data table need top-alignment to avoid
        # the table floating to the middle of the body area.
        has_table = "<table" in body_html
        body_cls  = "slide-body slide-body-table" if has_table else "slide-body"

        if i == 1:
            # ── Title slide: full navy background, centred ──────────────────
            slide = (
                f'<table class="slide slide-title">'
                f'<tr><td class="title-body">'
                f'<h1 class="title-h1">{title}</h1>'
                f'{body_html}'
                f'</td></tr>'
                f'{footer}'
                f'</table>'
            )
        elif not body_html:
            # ── Empty-body slides (e.g. "Questions?") — centre the title ───
            slide = (
                f'<table class="slide">'
                f'<tr><td class="slide-header">'
                f'<h1>{title}</h1>'
                f'</td></tr>'
                f'<tr><td class="slide-body slide-body-empty"></td></tr>'
                f'{footer}'
                f'</table>'
            )
        elif title:
            # ── Normal slide: header bar + body ────────────────────────────
            slide = (
                f'<table class="slide">'
                f'<tr><td class="slide-header"><h1>{title}</h1></td></tr>'
                f'<tr><td class="{body_cls}">{body_html}</td></tr>'
                f'{footer}'
                f'</table>'
            )
        else:
            # ── No title ────────────────────────────────────────────────────
            slide = (
                f'<table class="slide">'
                f'<tr><td class="{body_cls} slide-body-notitle">{body_html}</td></tr>'
                f'{footer}'
                f'</table>'
            )

        blocks.append(slide)

    return "\n".join(blocks)


def _render_document(raw: str, md_parser) -> str:
    return f'<div class="page">{md_parser.convert(raw)}</div>'


# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────

_SLIDE_CSS = f"""
@page {{
    size: 297mm 167mm;
    margin: 0;
}}

/* ── Layout table (one per slide) ─────────────────────── */
.slide {{
    page-break-after : always;
    border-collapse  : collapse;
    width            : 297mm;
    table-layout     : fixed;
    background-color : #ffffff;
}}
.slide:last-child {{ page-break-after: avoid; }}

/* ── Header bar ───────────────────────────────────────── */
.slide-header {{
    background-color : #1a3a6b;
    padding          : 0 40pt;
    height           : {_HEADER_H};
    vertical-align   : middle;
    border-bottom    : 3pt solid #4a90d9;
}}
.slide-header h1 {{
    color         : #ffffff;
    font-size     : 24pt;
    font-weight   : bold;
    margin        : 0;
    line-height   : 1.2;
    letter-spacing: -0.3pt;
}}

/* ── Body cell ────────────────────────────────────────── */
.slide-body {{
    padding        : 16pt 40pt;
    height         : {_BODY_H};
    vertical-align : middle;
    background-color: #ffffff;
}}
/* Table slides: align top so the table doesn't float to centre */
.slide-body-table {{
    vertical-align : top;
    padding-top    : 22pt;
}}
.slide-body-notitle {{
    padding-top: 28pt;
    height     : {int(int(_BODY_H.replace("pt","")) + int(_HEADER_H.replace("pt","")))}pt;
}}
.slide-body-empty {{
    height: {_BODY_H};
}}

/* ── Footer cell ──────────────────────────────────────── */
.slide-footer {{
    padding          : 0 40pt;
    height           : {_FOOTER_H};
    vertical-align   : middle;
    border-top       : 1pt solid #d1dae8;
    background-color : #f4f7fb;
}}
.slide-num {{
    color         : #7a8fa6;
    font-size     : 9pt;
    font-weight   : bold;
    letter-spacing: 1.5pt;
    text-transform: uppercase;
}}

/* ── Title slide ──────────────────────────────────────── */
.slide-title {{ background-color: #1a3a6b; }}
.slide-title .slide-footer {{
    background-color: #152f58;
    border-top      : 1pt solid #2a5298;
}}
.slide-title .slide-num {{ color: #5a80b0; }}

.title-body {{
    background-color : #1a3a6b;
    padding          : 50pt 60pt 20pt 60pt;
    height           : {_TITLE_H};
    vertical-align   : middle;
    text-align       : center;
}}
.title-h1 {{
    color         : #ffffff;
    font-size     : 38pt;
    font-weight   : bold;
    margin        : 0 0 22pt 0;
    line-height   : 1.15;
    letter-spacing: -1pt;
    border-bottom : 2pt solid #4a90d9;
    padding-bottom: 18pt;
    text-align    : center;
}}
.slide-title p {{
    color      : #a8c4e0;
    font-size  : 14pt;
    text-align : center;
    margin     : 6pt 0;
    line-height: 1.5;
}}
.slide-title em {{
    color      : #7eb8f0;
    font-style : normal;
    font-size  : 15pt;
    font-weight: bold;
}}

/* ── Headings inside body ─────────────────────────────── */
h2 {{
    font-size  : 17pt;
    color      : #1a3a6b;
    margin     : 0 0 9pt 0;
    padding-bottom: 5pt;
    border-bottom : 2pt solid #c5d8f0;
}}
h3 {{ font-size: 13pt; color: #2563eb; margin: 9pt 0 5pt 0; }}

/* ── Body text ────────────────────────────────────────── */
p      {{ font-size: 13pt; color: #2d3f55; line-height: 1.6; margin: 6pt 0; }}
strong {{ color: #1a3a6b; font-weight: bold; }}
em     {{ color: #4a6280; font-style: italic; }}

/* ── Lists ────────────────────────────────────────────── */
ul, ol {{ margin: 6pt 0; padding-left: 22pt; }}
li     {{ font-size: 13pt; color: #2d3f55; line-height: 1.65; margin-bottom: 9pt; }}
li strong {{ color: #1a3a6b; }}

/* ── Inline code ──────────────────────────────────────── */
code {{
    font-family     : "Courier New", Courier, monospace;
    font-size       : 11.5pt;
    background-color: #e8eef6;
    color           : #b01060;
    padding         : 1pt 4pt;
    border-radius   : 2pt;
}}

/* ── Code block ───────────────────────────────────────── */
pre {{
    background-color: #1e1e1e;
    color           : #d4d4d4;
    padding         : 12pt 16pt;
    font-size       : 11pt;
    font-family     : "Courier New", Courier, monospace;
    border-left     : 5pt solid #569cd6;
    border-top      : 1pt solid #333333;
    border-right    : 1pt solid #333333;
    border-bottom   : 1pt solid #333333;
    margin          : 8pt 0;
    white-space     : pre-wrap;
    line-height     : 1.7;
}}
pre code {{
    background-color: transparent;
    color           : #d4d4d4;
    padding         : 0;
    font-size       : 11pt;
}}

/* ── Blockquote ───────────────────────────────────────── */
blockquote {{
    background-color: #eaf2fb;
    border-left     : 4pt solid #2a6fc9;
    border-top      : 1pt solid #c5d8f0;
    border-bottom   : 1pt solid #c5d8f0;
    padding         : 10pt 16pt;
    margin          : 8pt 0;
    color           : #1e3a6b;
    font-style      : italic;
    font-size       : 13pt;
    line-height     : 1.55;
}}

/* ── Data tables (scoped so they don't affect layout tables) ── */
.data-table {{
    border-collapse : collapse;
    width           : 100%;
    table-layout    : auto;
    margin          : 8pt 0;
    font-size       : 22pt;
    word-wrap       : break-word;
}}
.data-table th {{
    background-color: #1a3a6b;
    color           : #ffffff;
    padding         : 10pt 14pt;
    text-align      : left;
    font-weight     : bold;
    border          : 1pt solid #0f2550;
    word-wrap       : break-word;
    vertical-align  : middle;
}}
.data-table td {{
    padding        : 9pt 14pt;
    color          : #2d3f55;
    border         : 1pt solid #d1dae8;
    word-wrap      : break-word;
    vertical-align : middle;
    line-height    : 1.5;
}}
.data-table tr:nth-child(even) td {{ background-color: #f0f5fb; }}
/* Inline code inside table cells — no highlight box */
.data-table code {{
    background-color: transparent;
    color           : #1a3a6b;
    font-weight     : bold;
    padding         : 0;
}}

hr {{ border: none; border-top: 1pt solid #d1dae8; margin: 10pt 0; }}
"""

_DOCUMENT_CSS = """
@page {
    size: A4;
    margin: 22mm 18mm 22mm 18mm;
}

.page { padding: 0; }

/* ── Headings ── */
h1 {
    font-size        : 22pt;
    color            : #ffffff;
    background-color : #1a3a6b;
    padding          : 14pt 18pt;
    margin           : 0 0 18pt 0;
    border-bottom    : 4pt solid #4a90d9;
    letter-spacing   : -0.5pt;
}
h2 {
    font-size    : 15pt;
    color        : #1a3a6b;
    margin       : 18pt 0 6pt 0;
    border-bottom: 1pt solid #c5d8f0;
    padding-bottom: 4pt;
}
h3 { font-size: 12pt; color: #2563eb; margin: 12pt 0 5pt 0; }
h4 { font-size: 11pt; color: #3b82f6; margin: 10pt 0 4pt 0; }

/* ── Body text ── */
p      { font-size: 11pt; color: #2d3f55; line-height: 1.65; margin: 6pt 0; }
strong { color: #1a3a6b; }
em     { color: #4a6280; }
a      { color: #2563eb; }

/* ── Lists ── */
ul, ol { margin: 6pt 0; padding-left: 22pt; }
li     { font-size: 11pt; color: #2d3f55; line-height: 1.6; margin: 3pt 0; }

/* ── Code ── */
pre {
    background-color: #0d1b2a;
    color           : #4ade80;
    padding         : 10pt;
    font-size       : 9pt;
    font-family     : "Courier New", Courier, monospace;
    border-left     : 4pt solid #10b981;
    margin          : 10pt 0;
    white-space     : pre-wrap;
}
code {
    font-family     : "Courier New", Courier, monospace;
    font-size       : 9pt;
    background-color: #e8eef6;
    color           : #b01060;
    padding         : 1pt 4pt;
}
pre code { background-color: transparent; color: #4ade80; padding: 0; }

/* ── Blockquote ── */
blockquote {
    background-color: #fefce8;
    border-left     : 4pt solid #f59e0b;
    padding         : 8pt 12pt;
    margin          : 10pt 0;
    color           : #78350f;
    font-style      : italic;
    font-size       : 10.5pt;
}

/* ── Tables ── */
table               { border-collapse: collapse; width: 100%; margin: 10pt 0; font-size: 10pt; }
th                  { background-color: #1a3a6b; color: #ffffff; padding: 6pt 10pt; text-align: left; font-weight: bold; border: 1pt solid #0f2550; }
td                  { padding: 6pt 10pt; color: #2d3f55; border: 1pt solid #d1dae8; }
tr:nth-child(even) td { background-color: #f0f5fb; }

hr { border: none; border-top: 2pt solid #d1dae8; margin: 14pt 0; }
"""


def _build_html(content_html: str, *, is_slides: bool) -> str:
    css = _SLIDE_CSS if is_slides else _DOCUMENT_CSS
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family     : Helvetica, Arial, sans-serif;
    color           : #1e293b;
    background-color: #ffffff;
    line-height     : 1.6;
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
