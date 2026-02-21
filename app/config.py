from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://toilets:toilets@localhost:5432/toilets"

    model_config = {"env_file": ".env"}


settings = Settings()
