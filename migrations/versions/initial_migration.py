"""Initial database migration

Revision ID: initial_migration
Create Date: 2025-05-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users table
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Assets table
    op.create_table('asset',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_identifier', sa.String(length=64), nullable=False),
        sa.Column('label', sa.String(length=128), nullable=True),
        sa.Column('asset_category', sa.String(length=64), nullable=True),
        sa.Column('asset_class', sa.String(length=64), nullable=True),
        sa.Column('asset_make', sa.String(length=64), nullable=True),
        sa.Column('asset_model', sa.String(length=64), nullable=True),
        sa.Column('serial_number', sa.String(length=128), nullable=True),
        sa.Column('device_serial_number', sa.String(length=128), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('days_inactive', sa.String(length=16), nullable=True),
        sa.Column('ignition', sa.Boolean(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('location', sa.String(length=256), nullable=True),
        sa.Column('site', sa.String(length=256), nullable=True),
        sa.Column('district', sa.String(length=64), nullable=True),
        sa.Column('sub_district', sa.String(length=64), nullable=True),
        sa.Column('engine_hours', sa.Float(), nullable=True),
        sa.Column('odometer', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('speed_limit', sa.Float(), nullable=True),
        sa.Column('heading', sa.String(length=16), nullable=True),
        sa.Column('backup_battery_pct', sa.Float(), nullable=True),
        sa.Column('voltage', sa.Float(), nullable=True),
        sa.Column('imei', sa.String(length=32), nullable=True),
        sa.Column('event_date_time', sa.DateTime(), nullable=True),
        sa.Column('event_date_time_string', sa.String(length=64), nullable=True),
        sa.Column('reason', sa.String(length=64), nullable=True),
        sa.Column('time_zone', sa.String(length=8), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asset_asset_category'), 'asset', ['asset_category'], unique=False)
    op.create_index(op.f('ix_asset_asset_identifier'), 'asset', ['asset_identifier'], unique=True)
    op.create_index(op.f('ix_asset_location'), 'asset', ['location'], unique=False)
    
    # Asset history table
    op.create_table('asset_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('location', sa.String(length=256), nullable=True),
        sa.Column('engine_hours', sa.Float(), nullable=True),
        sa.Column('odometer', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('voltage', sa.Float(), nullable=True),
        sa.Column('ignition', sa.Boolean(), nullable=True),
        sa.Column('event_date_time', sa.DateTime(), nullable=True),
        sa.Column('reason', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['asset.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Maintenance records table
    op.create_table('maintenance_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('service_type', sa.String(length=64), nullable=False),
        sa.Column('service_date', sa.DateTime(), nullable=False),
        sa.Column('engine_hours', sa.Float(), nullable=True),
        sa.Column('performed_by', sa.String(length=128), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['asset.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # API config table
    op.create_table('api_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('is_secret', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )


def downgrade():
    op.drop_table('maintenance_record')
    op.drop_table('asset_history')
    op.drop_index(op.f('ix_asset_location'), table_name='asset')
    op.drop_index(op.f('ix_asset_asset_identifier'), table_name='asset')
    op.drop_index(op.f('ix_asset_asset_category'), table_name='asset')
    op.drop_table('asset')
    op.drop_table('api_config')
    op.drop_table('user')