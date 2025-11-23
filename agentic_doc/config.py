from pathlib import Path

import yaml
from pydantic import BaseModel

CONFIG_FILENAME = ".agentic-doc.yml"


class Config(BaseModel):
    root_path: str = "."
    include_globs: list[str] = ["**/*"]
    exclude_globs: list[str] = [
        "**/node_modules/**",
        "**/.git/**",
        "**/__pycache__/**",
        "**/.venv/**",
    ]
    # LLM Configuration
    model_provider: str = "mock"  # openai, gemini, or mock

    # Provider specific settings can go here
    openai_model: str = "gpt-4o-mini"
    gemini_model: str = "gemini-2.5-flash"  # Free tier, fast model


def load_config(path: Path = Path(CONFIG_FILENAME)) -> Config:
    if not path.exists():
        return Config()

    with open(path) as f:
        data = yaml.safe_load(f)
        return Config(**(data or {}))


def save_config(config: Config, path: Path = Path(CONFIG_FILENAME)):
    with open(path, "w") as f:
        yaml.dump(config.model_dump(), f)
