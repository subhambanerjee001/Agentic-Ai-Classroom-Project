import os
import time
import logging
from openai import OpenAI
from crewai.llm import LLM
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Primary model from env, with automatic openrouter/ prefix
_raw_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
MODEL = _raw_model if _raw_model.startswith("openrouter/") else f"openrouter/{_raw_model}"

# Fallback chain — tried in order when a model is rate-limited
FALLBACK_MODELS = [
    MODEL,
    "openrouter/openai/gpt-oss-120b:free",
    "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    "openrouter/meta-llama/llama-3.3-70b-instruct:free",
    "openrouter/google/gemma-3-27b-it:free",
    "openrouter/meta-llama/llama-3.2-3b-instruct:free",
]
# Deduplicate while preserving order
_seen = set()
FALLBACK_MODELS = [
    m for m in FALLBACK_MODELS if not (m in _seen or _seen.add(m))
]

_RETRY_WAIT = 5   # seconds between retries on the same model
_MAX_RETRIES = 2  # retries per model before moving to the next


def create_llm(model: str = MODEL) -> LLM:
    return LLM(
        model=model,
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=16384,
    )


def kickoff_with_fallback(crew):
    """
    Run crew.kickoff() with automatic model fallback.
    On RateLimitError or NotFoundError, retries with the next model
    in FALLBACK_MODELS until one succeeds.
    """
    import litellm
    from .callbacks import crew_starting

    errors = []
    for model in FALLBACK_MODELS:
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                _set_crew_model(crew, model)
                crew.verbose = False
                crew_starting(crew, model)
                return crew.kickoff()
            except (litellm.RateLimitError, litellm.NotFoundError) as e:
                short = str(e)[:120]
                print(f"\n  [rate-limited] {model} -- trying next model...")
                errors.append(f"{model}: {short}")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_WAIT)
                break
            except Exception:
                raise

    raise RuntimeError("All models exhausted. Errors:\n" + "\n".join(errors))


def _set_crew_model(crew, model: str) -> None:
    """Replace the LLM on every agent in the crew."""
    llm = create_llm(model)
    for agent in crew.agents:
        agent.llm = llm


# ── Direct OpenAI-compat client (used outside CrewAI) ──────────────────────────

class ChatClient:
    def __init__(self, model: str = MODEL, api_key: str = OPENROUTER_API_KEY):
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def call(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=16384,
            temperature=0.7,
        )
        return response.choices[0].message.content
