"""Added timezone to vehicle settings

Revision ID: b117e50b5aa4
Revises: 3500b84eb1f1
Create Date: 2022-05-24 10:33:35.268307

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b117e50b5aa4'
down_revision = '3500b84eb1f1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('vehicle_settings', sa.Column('timezone', sa.String(length=256), nullable=True))


def downgrade():
    op.drop_column('vehicle_settings', 'timezone')

