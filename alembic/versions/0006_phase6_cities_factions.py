"""phase6 cities, factions, timed membership and territory

Revision ID: 0006_phase6
Revises: 0005_phase5
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_phase6"
down_revision: Union[str, Sequence[str], None] = "0005_phase5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("historical_name", sa.String(length=100), nullable=True),
        sa.Column("coord_x", sa.Integer(), nullable=True),
        sa.Column("coord_y", sa.Integer(), nullable=True),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("destroyed_year", sa.Integer(), nullable=True),
        sa.Column("historical_description", sa.Text(), nullable=True),
        sa.Column("population", sa.Integer(), nullable=False),
        sa.Column("military", sa.Integer(), nullable=False),
        sa.Column("economy", sa.Integer(), nullable=False),
        sa.Column("defense", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "code", name="uq_city_project_code"),
    )
    op.create_table(
        "factions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.Column("leader_character_id", sa.String(length=36), nullable=True),
        sa.Column("capital_city_id", sa.String(length=36), nullable=True),
        sa.Column("start_year", sa.Integer(), nullable=True),
        sa.Column("end_year", sa.Integer(), nullable=True),
        sa.Column("historical_description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["leader_character_id"], ["characters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["capital_city_id"], ["cities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "code", name="uq_faction_project_code"),
    )
    op.create_table(
        "faction_members",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("faction_id", sa.String(length=36), nullable=False),
        sa.Column("character_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("start_year", sa.Integer(), nullable=True),
        sa.Column("end_year", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["faction_id"], ["factions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "faction_territories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("faction_id", sa.String(length=36), nullable=False),
        sa.Column("city_id", sa.String(length=36), nullable=False),
        sa.Column("start_year", sa.Integer(), nullable=True),
        sa.Column("end_year", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["faction_id"], ["factions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("faction_territories")
    op.drop_table("faction_members")
    op.drop_table("factions")
    op.drop_table("cities")
