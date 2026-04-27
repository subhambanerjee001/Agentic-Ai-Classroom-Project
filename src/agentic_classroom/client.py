import os
from openai import OpenAI
from crewai.llm import LLM
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
_raw_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
MODEL = _raw_model if _raw_model.startswith("openrouter/") else f"openrouter/{_raw_model}"


def create_llm() -> LLM:
    return LLM(
        model=MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=16384,
    )


class ChatClient:
    """Direct OpenAI-compatible client for use outside CrewAI."""

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
