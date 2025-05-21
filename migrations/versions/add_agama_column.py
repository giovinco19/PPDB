"""add agama column

Revision ID: add_agama_column
Revises: create_created_at
Create Date: 2024-01-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_agama_column'
down_revision = 'create_created_at'
branch_labels = None
depends_on = None

def upgrade():
    # Tambah kolom agama ke tabel pendaftaran
    op.add_column('pendaftaran', sa.Column('agama', sa.String(20)))

def downgrade():
    # Hapus kolom agama jika rollback
    op.drop_column('pendaftaran', 'agama')
