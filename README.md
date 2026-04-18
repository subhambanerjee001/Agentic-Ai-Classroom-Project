# Agentic Classroom

An automated classroom simulation using CrewAI with three specialized agents that work together to create educational content.

## Overview

This project simulates a classroom environment with three AI agents:
- **Professor** - Creates comprehensive markdown slides from a topic
- **Teaching Assistant** - Creates quizzes and explanations based on the slides
- **Student** - Generates potential questions students might ask

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- OpenRouter API key (free at https://openrouter.ai)

## Installation

```bash
uv sync
```

## Configuration

### 1. Set API Key and Model

Edit the `.env` file in the project root:

```bash
# Get your free API key from https://openrouter.ai
OPENROUTER_API_KEY=your-api-key-here

# Choose a model from https://openrouter.ai/models
OPENROUTER_MODEL=openrouter/elephant-alpha
```

**Available Models** (working with this project):
- `openrouter/elephant-alpha` - Default, works well
- `gpt-4o-mini` - Fast and cheap
- `gpt-4o` - More capable
- `meta-llama/llama-3.1-70b-instruct` - Open source option

### 2. Set Topic

Edit `src/agentic_classroom/main.py` to set your topic:

```python
TOPIC = "Your Topic Here"
```

## Project Structure

```
agentic-classroom/
├── .env                       # API key and model configuration
├── pyproject.toml            # Project dependencies
├── README.md                 # This documentation
├── src/
│   └── agentic_classroom/
│       ├── __init__.py       # Package init
│       ├── client.py         # LLM client (reads from .env)
│       ├── agents.py         # Professor, TA, Student agents
│       ├── tasks.py          # Task definitions
│       └── main.py           # Main orchestration
└── output/                   # Generated files (created at runtime)
```

## How It Works

The workflow follows a sequential chain:

1. **Professor** receives a topic and creates markdown slides
2. **TA** receives the slides and creates a quiz with explanations
3. **Student** receives both slides and quiz, generating potential questions

Each agent uses OpenRouter API via CrewAI.

## Usage

```bash
uv run python -m agentic_classroom.main
```

## Example

With `TOPIC = "Python Generators"`, the following files are generated:

- `output/Python_Generators_slides.md` - Lecture slides (markdown)
- `output/Python_Generators_slides.pdf` - Lecture slides (PDF)
- `output/Python_Generators_quiz.md` - Quiz with explanations (markdown)
- `output/Python_Generators_quiz.pdf` - Quiz with explanations (PDF)
- `output/Python_Generators_questions.md` - Student questions (markdown)
- `output/Python_Generators_questions.pdf` - Student questions (PDF)

## Output Files

All generated content is saved to the `output/` directory with topic-based filenames. Each file contains:

- **Slides**: Well-structured markdown with headers, bullets, and code examples
- **Quiz**: Multiple choice and short answer questions with detailed explanations
- **Questions**: Organized by type (clarification, application, edge cases)

## Customization

You can modify:
- Agent backstories in `agents.py`
- Task descriptions in `tasks.py`
- Topic in `main.py` (TOPIC variable)
- Model and API key in `.env` file