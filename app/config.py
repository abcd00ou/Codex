from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = Field(default="deepseek", alias="LLM_PROVIDER")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_dep_ticket: str | None = Field(default=None, alias="OPENAI_DEP_TICKET")

    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")

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
