import hashlib
from typing import Optional
from sqlmodel import select
from agentic_doc.db.session import get_session
from agentic_doc.db.schema import LLMCache
from agentic_doc.llm.providers import ModelProvider, get_provider
from agentic_doc.config import Config

class LLMClient:
    def __init__(self, config: Config, db_session):
        self.config = config
        self.db = db_session
        
        # Select model based on provider
        if config.model_provider == "openai":
            model = config.openai_model
        elif config.model_provider == "gemini":
            model = config.gemini_model
        else:
            model = "mock"
        
        self.provider = get_provider(config.model_provider, model)

    def _hash_prompt(self, prompt: str, system_prompt: str) -> str:
        content = f"{system_prompt or ''}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def generate(self, prompt: str, system_prompt: Optional[str] = None, use_cache: bool = True) -> str:
        if use_cache:
            prompt_hash = self._hash_prompt(prompt, system_prompt or "")
            session_gen = get_session()
            session = next(session_gen)
            try:
                cached = session.exec(select(LLMCache).where(LLMCache.prompt_hash == prompt_hash)).first()
                if cached:
                    return cached.response
            finally:
                session.close()

        response = self.provider.generate(prompt, system_prompt)

        if use_cache:
            session_gen = get_session()
            session = next(session_gen)
            try:
                # Re-check cache to avoid race conditions (simple check)
                if not session.exec(select(LLMCache).where(LLMCache.prompt_hash == prompt_hash)).first():
                    cache_entry = LLMCache(
                        prompt_hash=prompt_hash,
                        model=getattr(self.provider, "model_name", "unknown"),  # Use model_name string, not model object
                        response=response
                    )
                    session.add(cache_entry)
                    session.commit()
            finally:
                session.close()
        
        return response
