"""Check invoices in database"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.invoice import Invoice

db = SessionLocal()
invoices = db.query(Invoice).all()

print(f'\nTotal invoices in database: {len(invoices)}\n')

if invoices:
    print('Invoice Details:')
    print('-' * 80)
    for inv in invoices:
        customer_name = inv.customer_snapshot.get('name', 'Unknown')
        print(f'{inv.invoice_number} | {customer_name} | ₹{inv.grand_total:.2f} | {inv.status} | Date: {inv.invoice_date}')
    print('-' * 80)
else:
    print('No invoices found in database.')

db.close()
