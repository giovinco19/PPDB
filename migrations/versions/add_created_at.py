from alembic import op
import sqlalchemy as sa
from datetime import datetime

def upgrade():
    # Add created_at column
    op.add_column('pendaftaran',
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

def downgrade():
    # Remove created_at column
    op.drop_column('pendaftaran', 'created_at')
