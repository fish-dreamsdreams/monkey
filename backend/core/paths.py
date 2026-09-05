"""仓库路径。

职责：为 Alembic CLI 与元信息接口提供稳定的项目根目录，不依赖当前工作目录。
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"
