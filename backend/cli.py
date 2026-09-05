"""命令行入口。

职责：提供 Windows 友好的数据库迁移命令，避免直接记忆 alembic 参数。
用法：python -m backend.cli db upgrade|current|history|check
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from alembic import command
from sqlalchemy import create_engine

from backend.core.alembic_runtime import build_alembic_config, script_head_revision
from backend.core.config import get_settings


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="python -m backend.cli",
        description="三国内容编辑器运维命令",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    db_parser = subparsers.add_parser("db", help="Alembic 数据库迁移")
    db_sub = db_parser.add_subparsers(dest="db_command", required=True)
    db_sub.add_parser("upgrade", help="升级到 head")
    db_sub.add_parser("current", help="显示数据库当前 revision")
    db_sub.add_parser("history", help="显示迁移历史")
    db_sub.add_parser("check", help="检查数据库是否已到达脚本 head")
    return parser


def _run_db_command(db_command: str) -> int:
    config = build_alembic_config()
    if db_command == "upgrade":
        command.upgrade(config, "head")
        return 0
    if db_command == "current":
        command.current(config)
        return 0
    if db_command == "history":
        command.history(config)
        return 0
    if db_command == "check":
        return _check_head(config)
    raise ValueError(f"未知 db 命令: {db_command}")


def _check_head(config: object) -> int:
    """比较数据库 current 与脚本 head。未对齐时返回退出码 1。"""
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext

    assert isinstance(config, Config)
    head = script_head_revision()
    engine = create_engine(get_settings().sync_database_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current = context.get_current_revision()
    if current == head:
        print(f"database is at head: {head}")
        return 0
    print(f"database revision mismatch: current={current} head={head}", file=sys.stderr)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    """CLI 主入口。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "db":
        return _run_db_command(args.db_command)
    parser.error(f"未知命令: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
