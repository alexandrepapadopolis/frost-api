from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://frost:frost@localhost:5432/frost"
    api_key_header: str = "X-API-Key"

    initial_api_key: str = "FROST-ESP32-CHAVE-001"
    initial_device_identifier: str = "SPLIT-001"
    initial_device_description: str = "Ar condicionado principal"
    initial_device_location: str = "Sala"
    initial_device_manufacturer: str = "DAIKIN"
    initial_device_model: str = "FTKP12S5VL"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
