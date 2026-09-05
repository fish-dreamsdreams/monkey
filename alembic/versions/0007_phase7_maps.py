"""phase7 maps, sparse terrain and vector features

Revision ID: 0007_phase7
Revises: 0006_phase6
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_phase7"
down_revision: Union[str, Sequence[str], None] = "0006_phase6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "maps",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("cell_size", sa.Integer(), nullable=False),
        sa.Column("default_terrain", sa.String(length=16), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "code", name="uq_map_project_code"),
    )
    op.create_table(
        "map_terrain_cells",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("map_id", sa.String(length=36), nullable=False),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.Column("terrain", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["map_id"], ["maps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("map_id", "x", "y", name="uq_terrain_map_xy"),
    )
    op.create_table(
        "map_features",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("map_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("feature_type", sa.String(length=16), nullable=False),
        sa.Column("geometry", sa.JSON(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["map_id"], ["maps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("map_id", "code", name="uq_feature_map_code"),
    )
    op.add_column("cities", sa.Column("map_id", sa.String(length=36), nullable=True))
    op.create_foreign_key("fk_cities_map_id", "cities", "maps", ["map_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_cities_map_id", "cities", type_="foreignkey")
    op.drop_column("cities", "map_id")
    op.drop_table("map_features")
    op.drop_table("map_terrain_cells")
    op.drop_table("maps")
