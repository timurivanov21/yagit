"""empty message.

Revision ID: 748fe98de655
Revises: 9244601f7ae6
Create Date: 2025-04-26 14:21:29.845409

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "748fe98de655"
down_revision = "9244601f7ae6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Run the migration."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "projects",
        sa.Column("gitlab_project_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("tracker_org_id", sa.Text(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Undo the migration."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("projects", "gitlab_project_id")
    op.drop_column("projects", "tracker_org_id")
    # ### end Alembic commands ###
