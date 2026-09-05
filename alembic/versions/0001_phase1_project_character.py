"""phase1 project and character tables

Revision ID: 0001_phase1
Revises:
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_phase1"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("content_version", sa.Integer(), nullable=False),
        sa.Column("target_start_year", sa.Integer(), nullable=True),
        sa.Column("target_end_year", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "personality_tags",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "code", name="uq_personality_tag_project_code"),
    )
    op.create_table(
        "characters",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("courtesy_name", sa.String(length=50), nullable=True),
        sa.Column("gender", sa.String(length=16), nullable=False),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("death_year", sa.Integer(), nullable=True),
        sa.Column("birthplace", sa.String(length=100), nullable=True),
        sa.Column("ethnicity", sa.String(length=50), nullable=True),
        sa.Column("identity", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "code", name="uq_character_project_code"),
    )
    op.create_table(
        "character_historical_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("character_id", sa.String(length=36), nullable=False),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("family_background", sa.Text(), nullable=True),
        sa.Column("life_experience", sa.Text(), nullable=True),
        sa.Column("achievements", sa.Text(), nullable=True),
        sa.Column("historical_evaluation", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("character_id"),
    )
    op.create_table(
        "character_attributes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("character_id", sa.String(length=36), nullable=False),
        sa.Column("version_name", sa.String(length=50), nullable=False),
        sa.Column("force", sa.Integer(), nullable=False),
        sa.Column("intelligence", sa.Integer(), nullable=False),
        sa.Column("politics", sa.Integer(), nullable=False),
        sa.Column("charisma", sa.Integer(), nullable=False),
        sa.Column("leadership", sa.Integer(), nullable=False),
        sa.Column("stamina", sa.Integer(), nullable=False),
        sa.Column("morale", sa.Integer(), nullable=False),
        sa.Column("mobility", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("character_id", "version_name", name="uq_character_attribute_version"),
    )
    op.create_table(
        "character_personalities",
        sa.Column("character_id", sa.String(length=36), primary_key=True),
        sa.Column("personality_tag_id", sa.String(length=36), primary_key=True),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["personality_tag_id"], ["personality_tags.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("character_personalities")
    op.drop_table("character_attributes")
    op.drop_table("character_historical_records")
    op.drop_table("characters")
    op.drop_table("personality_tags")
    op.drop_table("projects")
