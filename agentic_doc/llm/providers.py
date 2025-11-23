import os
from abc import ABC, abstractmethod


class ModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        pass


class OpenAIProvider(ModelProvider):
    def __init__(self, model: str = "gpt-4o"):
        from openai import OpenAI

        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = model
        self.model_name = model  # For cache storage

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        from agentic_doc.llm.api_tracker import get_tracker

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model, messages=messages
        )

        # Track API request
        get_tracker().increment("openai")

        return response.choices[0].message.content


class MockProvider(ModelProvider):
    def generate(self, _prompt: str, _system_prompt: str | None = None) -> str:
        return "Mock response: Documentation generated."


def get_provider(provider_name: str, model_name: str = "gpt-4o-mini") -> ModelProvider:
    """Get LLM provider by name."""
    if provider_name == "openai":
        return OpenAIProvider(model=model_name)
    elif provider_name == "gemini":
        from agentic_doc.llm.gemini_provider import GeminiProvider

        return GeminiProvider(model=model_name)
    elif provider_name == "mock":
        return MockProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
