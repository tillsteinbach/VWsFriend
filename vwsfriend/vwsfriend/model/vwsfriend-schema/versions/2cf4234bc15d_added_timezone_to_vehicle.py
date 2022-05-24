"""Added timezone to vehicle

Revision ID: 2cf4234bc15d
Revises: 3500b84eb1f1
Create Date: 2022-05-24 10:23:30.236042

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2cf4234bc15d'
down_revision = '3500b84eb1f1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('vehicles', sa.Column('timezone', sa.String(length=256), nullable=True))


def downgrade():
    op.drop_column('vehicles', 'timezone')

