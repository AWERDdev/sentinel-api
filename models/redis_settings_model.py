from pydantic_settings import BaseSettings , SettingsConfigDict

class redis_Settings(BaseSettings):
    HOST: str = "localhost"
    PORT: int = 6379
    DECODE_RESPONSE: bool = True
    ENCODING: str = "utf-8"
    MAX_REQUESTS: int = 5
    WINDOW_SECONDS: int = 60
    
    model_config = SettingsConfigDict(env_file=".env")
