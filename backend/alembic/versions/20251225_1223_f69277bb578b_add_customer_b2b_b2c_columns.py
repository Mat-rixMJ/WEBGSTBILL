"""add customer B2B/B2C columns

Revision ID: f69277bb578b
Revises: 
Create Date: 2025-12-25 12:23:47.041432

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f69277bb578b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to customers table
    op.add_column('customers', sa.Column('customer_type', sa.String(3), nullable=False, server_default='B2C'))
    op.add_column('customers', sa.Column('state_code', sa.String(2), nullable=False, server_default=''))
    
    # Create indexes for new columns
    op.create_index(op.f('ix_customers_state_code'), 'customers', ['state_code'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_customers_state_code'), table_name='customers')
    
    # Drop columns
    op.drop_column('customers', 'state_code')
    op.drop_column('customers', 'customer_type')
