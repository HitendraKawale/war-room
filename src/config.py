form pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    open_api_key: str = ""
    model_name: str = "gpt-4.1-mini"
    outputs_dir: str = "outputs"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

