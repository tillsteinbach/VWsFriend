"""change warning light unique constraint

Revision ID: 0e4da5320f4c
Revises: f69cf5eca1e2
Create Date: 2022-04-11 13:41:06.999090

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0e4da5320f4c'
down_revision = 'f69cf5eca1e2'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == 'postgresql':
        op.drop_constraint(None, 'warning_lights', type_='unique')
        op.create_unique_constraint(None, 'warning_lights', ['vehicle_vin', 'messageId', 'start'])


def downgrade():
    if op.get_context().dialect.name == 'postgresql':
        op.drop_constraint(None, 'warning_lights', type_='unique')
