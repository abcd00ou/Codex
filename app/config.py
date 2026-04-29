from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")

    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1", alias="GROQ_BASE_URL")
    groq_model: str = Field(default="openai/gpt-oss-120b", alias="GROQ_MODEL")

    xai_api_key: str | None = Field(default=None, alias="XAI_API_KEY")
    xai_base_url: str = Field(default="https://api.x.ai/v1", alias="XAI_BASE_URL")
    xai_model: str = Field(default="grok-4.20-reasoning", alias="XAI_MODEL")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-oss-120b", alias="OPENAI_MODEL")
    openai_dep_ticket: str | None = Field(default=None, alias="OPENAI_DEP_TICKET")

    mongodb_uri: str = Field(default="local://dev", alias="MONGODB_URI")
    mongodb_db: str = Field(default="agentic_ai", alias="MONGODB_DB")

    storage_dir: Path = Field(default=Path(".storage"), alias="STORAGE_DIR")
    max_chunk_chars: int = Field(default=3000, alias="MAX_CHUNK_CHARS")
    chunk_overlap_chars: int = Field(default=300, alias="CHUNK_OVERLAP_CHARS")
    parsing_agent_enabled: bool = Field(default=True, alias="PARSING_AGENT_ENABLED")
    parsing_agent_max_pages: int = Field(default=20, alias="PARSING_AGENT_MAX_PAGES")
    parsing_agent_max_chars_per_page: int = Field(default=12000, alias="PARSING_AGENT_MAX_CHARS_PER_PAGE")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings
