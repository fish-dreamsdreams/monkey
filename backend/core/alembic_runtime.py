"""Alembic 运行辅助。

职责：定位 alembic.ini、覆盖数据库 URL、查询脚本 head。不在应用启动时自动迁移。
"""

from alembic.config import Config
from alembic.script import ScriptDirectory

from backend.core.config import get_settings
from backend.core.paths import ALEMBIC_INI


def build_alembic_config() -> Config:
    """构造指向本仓库的 Alembic 配置。"""
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", get_settings().sync_database_url)
    config.set_main_option("script_location", str(ALEMBIC_INI.parent / "alembic"))
    return config


def script_head_revision() -> str:
    """读取迁移脚本的 head revision，不连接数据库。"""
    script = ScriptDirectory.from_config(build_alembic_config())
    head = script.get_current_head()
    if head is None:
        raise RuntimeError("未找到 Alembic head revision")
    return head
