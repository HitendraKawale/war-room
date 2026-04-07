from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_provider: str = "ollama"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3"

    open_api_key: str = ""
    model_name: str = "gpt-4.1-mini"

    outputs_dir: str = "outputs"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
