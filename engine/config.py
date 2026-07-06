from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Image2Model Engine"
    version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    upload_dir: Path = Path(__file__).parent / "uploads"
    test_svg_dir: Path = Path(__file__).parent.parent / "test-svgs"

    max_upload_size_mb: int = 50
    task_timeout_seconds: int = 300


settings = Settings()
