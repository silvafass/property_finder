from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)
from typing import List, Optional, Type, Tuple


class SearchSettings(BaseSettings):
    locations: List[str] = []
    property_types: List[str] = []
    maximum_price: Optional[float] = None
    maximum_condominium_fee: Optional[float] = None
    include_condominium_fee: Optional[bool] = None
    minimum_square_meter: Optional[int] = None
    maximum_square_meter: Optional[int] = None
    bathrooms: List[int] = []
    bedrooms: List[int] = []


class PublisherSettings(BaseSettings):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _buying_search = self.buying_search.model_dump(
            exclude_none=True, exclude_defaults=True
        )
        for key, value in self.base_search.model_dump(
            exclude_none=True, exclude_defaults=True
        ).items():
            if _buying_search.get(key) is None:
                setattr(self.buying_search, key, value)
        _renting_search = self.renting_search.model_dump(
            exclude_none=True, exclude_defaults=True
        )
        for key, value in self.base_search.model_dump(
            exclude_none=True, exclude_defaults=True
        ).items():
            if _renting_search.get(key) is None:
                setattr(self.renting_search, key, value)

    only_inspect: bool = True
    always_download_pictures: bool = False
    base_search: SearchSettings = SearchSettings()
    buying_search: SearchSettings = SearchSettings()
    renting_search: SearchSettings = SearchSettings()

    model_config = SettingsConfigDict(yaml_file="config/default.yaml")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        **args,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (YamlConfigSettingsSource(settings_cls),)


class Settings(BaseSettings):
    db_connection_uri: str = "sqlite:///data.db"
    db_echo: bool = False

    browser_headless: bool = False
    browser_channel: str = "firefox"
    # browser_args: List[str] = ["--start-maximized"]
    browser_args: List[str] = []
    # browser_no_viewport: bool = True
    browser_no_viewport: bool = False

    default_publisher_settings: PublisherSettings = PublisherSettings()

    model_config = SettingsConfigDict(env_file=".env")
