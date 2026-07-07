from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Kidney Disease Detection using Deep Learning"
    environment: str = "development"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/kidney_ai"
    model_path: str = "backend/model/gradcam_resnet34_full.pth"
    allowed_origins_raw: str = Field(
        default="http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000",
        alias="ALLOWED_ORIGINS",
    )
    max_upload_mb: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]

    @property
    def resolved_model_path(self) -> Path:
        path = Path(self.model_path)
        if path.is_absolute():
            return path
        candidates = [
            Path.cwd() / path,
            Path.cwd() / "model" / "gradcam_resnet34_full.pth",
            Path(__file__).resolve().parents[3] / path,
            Path(__file__).resolve().parents[2] / "model" / "gradcam_resnet34_full.pth",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

