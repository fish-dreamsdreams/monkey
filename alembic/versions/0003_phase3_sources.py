"""phase3 sources catalog, citations, personality description

Revision ID: 0003_phase3
Revises: 0002_phase2
Create Date: 2026-09-05
"""

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0003_phase3"
down_revision: Union[str, Sequence[str], None] = "0002_phase2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SYSTEM_SOURCES = (
    ("sanguozhi", "三国志", "official_history"),
    ("houhanshu", "后汉书", "official_history"),
    ("zizhitongjian", "资治通鉴", "historical_book"),
    ("sanguoyanyi", "三国演义", "literary"),
    ("game_setting", "游戏设定", "game_setting"),
)

_TAG_DESCRIPTIONS = (
    ("brave", "临阵敢进，不避锋镝"),
    ("cautious", "行事稳妥，先计后动"),
    ("suspicious", "对人与局势常存戒心"),
    ("loyal", "重恩义，不易改事他主"),
    ("decisive", "能迅速决断并执行"),
    ("benevolent", "待人宽厚，能收士心"),
    ("cunning", "善权谋，不拘常法"),
    ("ambitious", "有扩张权势的强烈意愿"),
    ("calm", "危局中仍能保持理智"),
)


def upgrade() -> None:
    op.add_column("personality_tags", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "character_personalities",
        sa.Column("intensity", sa.Integer(), nullable=False, server_default="3"),
    )
    op.create_table(
        "sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "code", name="uq_source_project_code"),
    )
    op.create_table(
        "character_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("character_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("bound_layer", sa.String(length=16), nullable=False),
        sa.Column("quotation", sa.Text(), nullable=True),
        sa.Column("reference", sa.String(length=200), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    bind = op.get_bind()
    for code, description in _TAG_DESCRIPTIONS:
        bind.execute(
            sa.text(
                "UPDATE personality_tags SET description = :description "
                "WHERE code = :code AND is_system = 1"
            ),
            {"description": description, "code": code},
        )
    projects = bind.execute(sa.text("SELECT id FROM projects")).fetchall()
    for row in projects:
        project_id = str(row[0])
        for code, name, source_type in _SYSTEM_SOURCES:
            bind.execute(
                sa.text(
                    "INSERT INTO sources (id, project_id, code, name, source_type, is_system) "
                    "VALUES (:id, :project_id, :code, :name, :source_type, 1)"
                ),
                {
                    "id": f"src_{uuid4().hex}",
                    "project_id": project_id,
                    "code": code,
                    "name": name,
                    "source_type": source_type,
                },
            )


def downgrade() -> None:
    op.drop_table("character_sources")
    op.drop_table("sources")
    op.drop_column("character_personalities", "intensity")
    op.drop_column("personality_tags", "description")
