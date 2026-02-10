from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite+aiosqlite:///./task_manager.db"
    admin_username: str = "admin"
    admin_password: str = "admin666"
    auth_secret: str = "change-me-in-production"
    auth_token_expire_minutes: int = 1440
    upload_api_base_url: str = "http://api.test-hot-product.echooo.link"
    log_level: str = "INFO"
    log_dir: str = "logs"

    max_image_size_mb: int = 10
    max_images_per_subtask: int = 10

    cors_origins: str = "http://localhost:5173"
    auto_create_tables: bool = True

    @property
    def max_image_size_bytes(self) -> int:
        return self.max_image_size_mb * 1024 * 1024

    @property
    def upload_api_url(self) -> str:
        return f"{self.upload_api_base_url.rstrip('/')}/api/v1/video/upload-image"

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
