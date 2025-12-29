"""Add invoice contract fields and gst_amount to items

Revision ID: add_invoice_contract_fields
Revises: 20251225_1223_f69277bb578b_add_customer_b2b_b2c_columns
Create Date: 2025-12-26 12:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_invoice_contract_fields'
down_revision = 'f69277bb578b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # invoices table additions
    op.add_column('invoices', sa.Column('place_of_supply', sa.String(length=100), nullable=False, server_default='UNKNOWN'))
    op.add_column('invoices', sa.Column('invoice_type', sa.String(length=20), nullable=False, server_default='TAX_INVOICE'))
    op.add_column('invoices', sa.Column('status', sa.String(length=20), nullable=False, server_default='FINAL'))
    op.add_column('invoices', sa.Column('finalized_at', sa.DateTime(), nullable=True))
    op.add_column('invoices', sa.Column('total_taxable_value_paise', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('invoices', sa.Column('total_gst_paise', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('invoices', sa.Column('grand_total_paise', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('invoices', sa.Column('round_off_paise', sa.Integer(), nullable=False, server_default='0'))

    # invoice_items table additions
    op.add_column('invoice_items', sa.Column('gst_amount_paise', sa.Integer(), nullable=False, server_default='0'))

    # cleanup defaults for new columns
    op.execute("UPDATE invoices SET place_of_supply = COALESCE(place_of_supply, 'UNKNOWN')")


def downgrade() -> None:
    op.drop_column('invoice_items', 'gst_amount_paise')
    op.drop_column('invoices', 'round_off_paise')
    op.drop_column('invoices', 'grand_total_paise')
    op.drop_column('invoices', 'total_gst_paise')
    op.drop_column('invoices', 'total_taxable_value_paise')
    op.drop_column('invoices', 'finalized_at')
    op.drop_column('invoices', 'status')
    op.drop_column('invoices', 'invoice_type')
    op.drop_column('invoices', 'place_of_supply')
