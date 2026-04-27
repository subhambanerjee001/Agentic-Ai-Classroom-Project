import os
import re

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from .renderer import convert_to_pdf, generate_interactive_slides

OUTPUT_DIR = "output"


class CreatePresentationInput(BaseModel):
    topic: str = Field(..., description="Topic of the presentation")
    slides_markdown: str = Field(
        ..., description="Full markdown slides content with slides separated by ---"
    )


class CreatePresentationTool(BaseTool):
    name: str = "create_presentation"
    description: str = (
        "Saves the finished slides as a PDF and an interactive HTML presentation. "
        "Call this once you have completed writing all the slides markdown."
    )
    args_schema: type[BaseModel] = CreatePresentationInput

    def _run(self, topic: str, slides_markdown: str) -> str:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        safe = re.sub(r"[^\w\s-]", "_", topic).strip().replace(" ", "_")

        md_path = f"{OUTPUT_DIR}/{safe}_slides.md"
        with open(md_path, "w") as f:
            f.write(slides_markdown)

        html_path = generate_interactive_slides(md_path)
        pdf_path = convert_to_pdf(md_path, is_slides=True)

        return (
            f"Presentation files created:\n"
            f"  Markdown : {md_path}\n"
            f"  HTML     : {html_path}\n"
            f"  PDF      : {pdf_path}"
        )
