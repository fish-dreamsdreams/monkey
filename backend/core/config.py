"""应用配置。

职责：从环境变量加载 MySQL 连接信息，不把密钥写进代码。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """运行时配置。"""

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "sanguo"
    mysql_password: str = "sanguo"
    mysql_database: str = "sanguo_editor"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """SQLAlchemy 异步连接串（运行时使用）。"""
        return (
            f"mysql+asyncmy://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )

    @property
    def sync_database_url(self) -> str:
        """Alembic 同步连接串。"""
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例。"""
    return Settings()
