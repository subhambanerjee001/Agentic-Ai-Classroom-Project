from openai import OpenAI
from crewai.llm import LLM
import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/elephant-alpha")


def read_b64(path: str) -> str:
    with open(path, "rb") as f:
        import base64

        return base64.b64encode(f.read()).decode()


class ChatClient:
    def __init__(self, model: str = MODEL, api_key: str = OPENROUTER_API_KEY):
        self.model = model
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
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
            temperature=1.00,
        )

        return response.choices[0].message.content


def create_llm() -> LLM:
    return LLM(
        model=MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=1.00,
        max_tokens=16384,
    )
