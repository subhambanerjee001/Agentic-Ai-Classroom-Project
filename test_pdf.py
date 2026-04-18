from src.agentic_classroom.main import convert_to_pdf, _build_html
import markdown as md_lib
from pathlib import Path
import re

md_path = "output/AI_Agent_slides.md"
raw = Path(md_path).read_text(encoding="utf-8")

md_parser = md_lib.Markdown(extensions=["tables", "fenced_code", "codehilite", "nl2br", "sane_lists"])
sections = [s.strip() for s in re.split(r"^---\s*$", raw, flags=re.MULTILINE)]
sections = [s for s in sections if s]

total = len(sections)
html_blocks = []
for i, section in enumerate(sections, start=1):
    md_parser.reset()
    body = md_parser.convert(section)
    html_blocks.append(
        f'<div class="slide">'
        f'{body}'
        f'<div class="slide-number">{i} / {total}</div>'
        f'</div>'
    )
content_html = "\n".join(html_blocks)

styled_html = _build_html(content_html, is_slides=True)
# patch size
styled_html = styled_html.replace('size: A4;', 'size: 12in 6.75in;')

from weasyprint import HTML
HTML(string=styled_html, base_url="output").write_pdf("test_landscape.pdf")
