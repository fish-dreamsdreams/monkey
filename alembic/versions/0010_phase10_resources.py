"""phase10 resource and model asset metadata

Revision ID: 0010_phase10
Revises: 0009_phase9
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_phase10"
down_revision: Union[str, Sequence[str], None] = "0009_phase9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=32), nullable=False),
        sa.Column("path", sa.String(length=200), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("preview_path", sa.String(length=200), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "code", name="uq_resource_project_code"),
    )
    op.create_table(
        "model_assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("resource_id", sa.String(length=36), nullable=False),
        sa.Column("mesh_format", sa.String(length=16), nullable=False),
        sa.Column("lod_count", sa.Integer(), nullable=False),
        sa.Column("animation_set_note", sa.Text(), nullable=True),
        sa.Column("skeleton_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["resource_id"], ["resources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resource_id"),
    )
    op.add_column("characters", sa.Column("portrait_asset_id", sa.String(length=36), nullable=True))
    op.add_column("characters", sa.Column("model_asset_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_characters_portrait_asset_id",
        "characters",
        "resources",
        ["portrait_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_characters_model_asset_id",
        "characters",
        "resources",
        ["model_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column("skills", sa.Column("icon_asset_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_skills_icon_asset_id",
        "skills",
        "resources",
        ["icon_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column("cities", sa.Column("icon_asset_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_cities_icon_asset_id",
        "cities",
        "resources",
        ["icon_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column("maps", sa.Column("preview_asset_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_maps_preview_asset_id",
        "maps",
        "resources",
        ["preview_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_maps_preview_asset_id", "maps", type_="foreignkey")
    op.drop_column("maps", "preview_asset_id")
    op.drop_constraint("fk_cities_icon_asset_id", "cities", type_="foreignkey")
    op.drop_column("cities", "icon_asset_id")
    op.drop_constraint("fk_skills_icon_asset_id", "skills", type_="foreignkey")
    op.drop_column("skills", "icon_asset_id")
    op.drop_constraint("fk_characters_model_asset_id", "characters", type_="foreignkey")
    op.drop_constraint("fk_characters_portrait_asset_id", "characters", type_="foreignkey")
    op.drop_column("characters", "model_asset_id")
    op.drop_column("characters", "portrait_asset_id")
    op.drop_table("model_assets")
    op.drop_table("resources")
