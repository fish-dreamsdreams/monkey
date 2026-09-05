"""phase4 character relationships

Revision ID: 0004_phase4
Revises: 0003_phase3
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_phase4"
down_revision: Union[str, Sequence[str], None] = "0003_phase3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "character_relationships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("pair_id", sa.String(length=36), nullable=False),
        sa.Column("from_character_id", sa.String(length=36), nullable=False),
        sa.Column("to_character_id", sa.String(length=36), nullable=False),
        sa.Column("relationship_type", sa.String(length=32), nullable=False),
        sa.Column("intimacy", sa.Integer(), nullable=False),
        sa.Column("hostility", sa.Integer(), nullable=False),
        sa.Column("start_year", sa.Integer(), nullable=True),
        sa.Column("end_year", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_character_relationships_pair_id", "character_relationships", ["pair_id"])
    op.create_index(
        "ix_character_relationships_from_character_id",
        "character_relationships",
        ["from_character_id"],
    )
    op.create_index(
        "ix_character_relationships_to_character_id",
        "character_relationships",
        ["to_character_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_character_relationships_to_character_id", table_name="character_relationships")
    op.drop_index("ix_character_relationships_from_character_id", table_name="character_relationships")
    op.drop_index("ix_character_relationships_pair_id", table_name="character_relationships")
    op.drop_table("character_relationships")
