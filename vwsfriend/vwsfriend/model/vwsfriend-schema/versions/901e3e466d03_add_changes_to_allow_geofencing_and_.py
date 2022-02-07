"""Add changes to allow geofencing and custom chargers / operators

Revision ID: 901e3e466d03
Revises: eb4c7c65c4fb
Create Date: 2022-02-07 08:46:25.177834

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '901e3e466d03'
down_revision = 'eb4c7c65c4fb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('geofences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('radius', sa.Float(), nullable=True),
    sa.Column('location_id', sa.BigInteger(), nullable=True),
    sa.Column('charger_id', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['charger_id'], ['chargers.id'], ),
    sa.ForeignKeyConstraint(['location_id'], ['locations.osm_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('chargers', sa.Column('custom', sa.Boolean(), nullable=True))
    op.execute("UPDATE chargers SET custom = false")
    op.add_column('operators', sa.Column('custom', sa.Boolean(), nullable=True))
    op.execute("UPDATE operators SET custom = false")

    if op.get_context().dialect.name == 'postgresql':
        op.execute(sa.text('CREATE extension IF NOT EXISTS cube;'))
        op.execute(sa.text('CREATE extension IF NOT EXISTS earthdistance;'))


def downgrade():
    op.drop_column('operators', 'custom')
    op.drop_column('chargers', 'custom')
    op.drop_table('geofences')
