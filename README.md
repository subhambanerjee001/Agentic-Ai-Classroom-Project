# Agentic Classroom

An automated classroom simulation using CrewAI with three specialized agents that collaborate to generate a full set of educational content from a single topic.

## Overview

The workflow runs four agents in sequence:

1. **Professor** — creates structured markdown slides
2. **Teaching Assistant** — writes a quiz with explanations based on the slides
3. **Student** — generates clarification, application, and edge-case questions
4. **Teaching Assistant** — answers all student questions in detail

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenRouter API key (free tier available at https://openrouter.ai)

## Installation

```bash
uv sync
```

## Configuration

### 1. Create your `.env` file

Copy the provided template and fill in your API key:

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholder:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-oss-120b:free
```

The `openrouter/` prefix is added automatically — use the model ID exactly as shown on https://openrouter.ai/models.

### 2. Set the topic

Edit `src/agentic_classroom/main.py`:

```python
TOPIC = "Your Topic Here"
```

## Usage

```bash
uv run python -m agentic_classroom.main
```

## Output

All files are written to `output/` with topic-based names. For `TOPIC = "API in python"`:

| File | Description |
|------|-------------|
| `API_in_python_slides.md` | Lecture slides (markdown) |
| `API_in_python_slides.pdf` | Lecture slides (PDF) |
| `API_in_python_slides_interactive.html` | Reveal.js presentation |
| `API_in_python_quiz.md / .pdf` | Quiz with explanations |
| `API_in_python_questions.md / .pdf` | Student questions |
| `API_in_python_answers.md / .pdf` | TA answers |
| `*_visualization.html` | CrewAI flow diagrams |

## Project Structure

```
agentic-classroom/
├── .env                        # Your API key and model (gitignored)
├── .env.example                # Template — copy to .env to get started
├── pyproject.toml
├── src/
│   └── agentic_classroom/
│       ├── main.py             # Orchestration — set TOPIC here
│       ├── agents.py           # Professor, TA, Student agent definitions
│       ├── tasks.py            # Task prompts and templates
│       ├── client.py           # LLM client with automatic model fallback
│       ├── renderer.py         # Markdown -> PDF and Reveal.js HTML
│       ├── visualization.py    # CrewAI flow diagram export
│       └── callbacks.py        # Terminal status display
└── output/                     # Generated files (created at runtime)
```

## Model Fallback

If the primary model is rate-limited, the client automatically tries the next model in the fallback chain defined in `client.py`. To check which free models are currently available:

```bash
uv run python -c "
import urllib.request, json
req = urllib.request.Request('https://openrouter.ai/api/v1/models')
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
free = [m['id'] for m in data['data'] if str(m.get('pricing',{}).get('prompt','1')) == '0']
print('\n'.join(sorted(free)))
"
```
