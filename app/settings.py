from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_connection_uri: str = "sqlite:///data.db"
    db_echo: bool = True

    browser_headless: bool = False
    browser_channel: str = "chromium"
    browser_args: list[str] = ["--start-maximized"]
    browser_no_viewport: bool = True

    model_config = SettingsConfigDict(env_file=".env")
