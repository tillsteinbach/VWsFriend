"""Add missing ENUM

Revision ID: eb4c7c65c4fb
Revises: 1b71c67dd2eb
Create Date: 2022-02-04 20:04:08.442697

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb4c7c65c4fb'
down_revision = '1b71c67dd2eb'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == 'postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE chargingstate ADD VALUE IF NOT EXISTS 'CONSERVATION'")


def downgrade():
    pass
