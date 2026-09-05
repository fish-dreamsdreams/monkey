"""仓库路径。

职责：为 Alembic CLI 与元信息接口提供稳定的项目根目录，不依赖当前工作目录。
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"
PROJECT_ASSETS_ROOT = REPO_ROOT / "var" / "projects"


def project_assets_dir(project_id: str) -> Path:
    """用户项目资源根目录。不是编辑器自身 assets。"""
    return PROJECT_ASSETS_ROOT / project_id / "assets"
