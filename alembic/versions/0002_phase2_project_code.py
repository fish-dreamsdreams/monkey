"""phase2 add project business code

Revision ID: 0002_phase2
Revises: 0001_phase1
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_phase2"
down_revision: Union[str, Sequence[str], None] = "0001_phase1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("code", sa.String(length=64), nullable=True))
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id FROM projects WHERE code IS NULL")).fetchall()
    for row in rows:
        project_id = str(row[0])
        code = "proj_" + project_id.replace("-", "")[:16]
        bind.execute(
            sa.text("UPDATE projects SET code = :code WHERE id = :id"),
            {"code": code, "id": project_id},
        )
    op.alter_column(
        "projects",
        "code",
        existing_type=sa.String(length=64),
        nullable=False,
        existing_nullable=True,
    )
    op.create_unique_constraint("uq_projects_code", "projects", ["code"])


def downgrade() -> None:
    op.drop_constraint("uq_projects_code", "projects", type_="unique")
    op.drop_column("projects", "code")
