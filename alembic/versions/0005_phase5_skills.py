"""phase5 skills and character skill bindings

Revision ID: 0005_phase5
Revises: 0004_phase4
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_phase5"
down_revision: Union[str, Sequence[str], None] = "0004_phase4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("skill_type", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target", sa.String(length=32), nullable=False),
        sa.Column("cooldown", sa.Integer(), nullable=False),
        sa.Column("cost", sa.JSON(), nullable=False),
        sa.Column("trigger_condition", sa.JSON(), nullable=True),
        sa.Column("effects", sa.JSON(), nullable=False),
        sa.Column("basis_source_type", sa.String(length=32), nullable=True),
        sa.Column("basis_source_code", sa.String(length=64), nullable=True),
        sa.Column("basis_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "code", name="uq_skill_project_code"),
    )
    op.create_table(
        "character_skills",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("character_id", sa.String(length=36), nullable=False),
        sa.Column("skill_id", sa.String(length=36), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("source_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("character_id", "skill_id", name="uq_character_skill"),
    )


def downgrade() -> None:
    op.drop_table("character_skills")
    op.drop_table("skills")
