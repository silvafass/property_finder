from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_connection_uri: str = "sqlite:///data.db"
    db_echo: bool = False

    browser_headless: bool = False
    browser_channel: str = "chromium"
    # browser_args: list[str] = ["--start-maximized"]
    browser_args: list[str] = []
    # browser_no_viewport: bool = True
    browser_no_viewport: bool = False

    model_config = SettingsConfigDict(env_file=".env")
