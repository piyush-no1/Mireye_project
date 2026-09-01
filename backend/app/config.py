from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    cors_allowed_origins: str = "http://localhost:5173"

    openai_api_key: str = "mock-openai-key"
    openai_model: str = "gpt-5.5"
    openai_request_timeout_seconds: int = 30

    mireye_api_key: str = "mock-mireye-key"
    mireye_base_url: str = "https://api.mireye.com/v1"

    usgs_nldi_base_url: str = "https://labs.waterdata.usgs.gov/api/nldi"
    usgs_nwis_base_url: str = "https://waterservices.usgs.gov/nwis/iv"
    epa_wqp_base_url: str = "https://www.waterqualitydata.usgs.gov/data"
    epa_attains_base_url: str = "https://api.epa.gov/attains"
    epa_attains_api_key: str = ""
    epa_echo_base_url: str = "https://echodata.epa.gov/echo"
    epa_tri_base_url: str = "https://enviro.epa.gov/enviro/efservice/tri_facility"
    usda_cropscape_base_url: str = "https://nassgeodata.gmu.edu/CropScape/dev"
    copernicus_client_id: str = ""
    copernicus_client_secret: str = ""

    http_timeout_seconds: int = 15
    http_timeout_seconds_long: int = 30
    http_max_retries: int = 2
    http_retry_backoff_base_seconds: float = 0.5

    output_dir: str = "./data/outputs"

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()
