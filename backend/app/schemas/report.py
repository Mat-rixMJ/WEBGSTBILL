"""Report schemas for GST billing system"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class SalesRegisterRow(BaseModel):
    """Single row in sales register report"""
    invoice_number: str
    invoice_date: date
    customer_name: str
    customer_gstin: Optional[str] = None
    place_of_supply: str
    taxable_value: float = Field(..., description="Taxable amount in rupees")
    cgst: float = Field(..., description="CGST amount in rupees")
    sgst: float = Field(..., description="SGST amount in rupees")
    igst: float = Field(..., description="IGST amount in rupees")
    total_gst: float = Field(..., description="Total GST in rupees")
    grand_total: float = Field(..., description="Grand total in rupees")
    status: str = Field(..., description="FINAL or CANCELLED")


class SalesRegisterSummary(BaseModel):
    """Totals for sales register"""
    total_taxable_value: float
    total_cgst: float
    total_sgst: float
    total_igst: float
    total_gst: float
    total_grand_total: float
    count_invoices: int
    count_cancelled: int


class SalesRegisterResponse(BaseModel):
    """Complete sales register report"""
    from_date: date
    to_date: date
    rows: List[SalesRegisterRow]
    summary: SalesRegisterSummary


class PurchaseRegisterRow(BaseModel):
    """Single row in purchase register report"""
    supplier_name: str
    supplier_gstin: Optional[str] = None
    supplier_invoice_number: str
    invoice_date: date
    taxable_value: float = Field(..., description="Taxable amount in rupees")
    input_cgst: float = Field(..., description="Input CGST in rupees")
    input_sgst: float = Field(..., description="Input SGST in rupees")
    input_igst: float = Field(..., description="Input IGST in rupees")
    total_input_gst: float = Field(..., description="Total input GST in rupees")
    grand_total: float = Field(..., description="Grand total in rupees")
    status: str = Field(..., description="FINAL or CANCELLED")


class PurchaseRegisterSummary(BaseModel):
    """Totals for purchase register"""
    total_taxable_value: float
    total_input_cgst: float
    total_input_sgst: float
    total_input_igst: float
    total_input_gst: float
    total_grand_total: float
    count_purchases: int
    count_cancelled: int


class PurchaseRegisterResponse(BaseModel):
    """Complete purchase register report"""
    from_date: date
    to_date: date
    rows: List[PurchaseRegisterRow]
    summary: PurchaseRegisterSummary


class GSTSummaryOutput(BaseModel):
    """Output GST (Sales) summary"""
    cgst: float
    sgst: float
    igst: float
    total: float


class GSTSummaryInput(BaseModel):
    """Input GST (Purchases) summary"""
    cgst: float
    sgst: float
    igst: float
    total: float


class GSTSummaryResponse(BaseModel):
    """Monthly GST summary report"""
    month: int = Field(..., ge=1, le=12)
    year: int
    output_gst: GSTSummaryOutput
    input_gst: GSTSummaryInput
    sales_count: int
    purchase_count: int

class CustomerReportRow(BaseModel):
    """Single row in customer-wise sales report"""
    customer_id: int
    customer_name: str
    customer_type: str = Field(..., description="B2B or B2C")
    customer_gstin: Optional[str] = None
    total_invoices: int
    total_sales_value: float = Field(..., description="Total sales in rupees")
    total_taxable_value: float
    total_cgst: float
    total_sgst: float
    total_igst: float
    total_gst_collected: float


class CustomerReportSummary(BaseModel):
    """Totals for customer report"""
    total_customers: int
    total_invoices: int
    b2b_sales: float
    b2c_sales: float
    total_sales_value: float
    total_taxable_value: float
    total_gst_collected: float


class CustomerReportResponse(BaseModel):
    """Complete customer-wise sales report"""
    from_date: date
    to_date: date
    rows: List[CustomerReportRow]
    summary: CustomerReportSummary


class SupplierReportRow(BaseModel):
    """Single row in supplier-wise purchase report"""
    supplier_id: int
    supplier_name: str
    supplier_type: str = Field(..., description="Registered or Unregistered")
    supplier_gstin: Optional[str] = None
    total_purchases: int
    total_purchase_value: float
    total_taxable_value: float
    total_input_cgst: float
    total_input_sgst: float
    total_input_igst: float
    total_input_gst_paid: float


class SupplierReportSummary(BaseModel):
    """Totals for supplier report"""
    total_suppliers: int
    total_purchases: int
    registered_purchases: float
    unregistered_purchases: float
    total_purchase_value: float
    total_input_gst_paid: float


class SupplierReportResponse(BaseModel):
    """Complete supplier-wise purchase report"""
    from_date: date
    to_date: date
    rows: List[SupplierReportRow]
    summary: SupplierReportSummary


class ProductHSNReportRow(BaseModel):
    """Single row in product/HSN report"""
    product_id: int
    product_name: str
    hsn_code: str
    gst_rate: int = Field(..., description="GST rate in %")
    quantity_sold: float
    unit: str
    taxable_value: float
    total_gst_collected: float


class ProductHSNReportSummary(BaseModel):
    """Totals for product/HSN report"""
    total_products: int
    total_quantity: float
    total_taxable_value: float
    total_gst_collected: float


class ProductHSNReportResponse(BaseModel):
    """Complete product/HSN report (for GSTR-1 prep)"""
    from_date: date
    to_date: date
    rows: List[ProductHSNReportRow]
    summary: ProductHSNReportSummary


class InventoryReportRow(BaseModel):
    """Single row in inventory report"""
    product_id: int
    product_name: str
    hsn_code: str
    unit: str
    opening_stock: float
    purchased_quantity: float
    sold_quantity: float
    closing_stock: float


class InventoryReportResponse(BaseModel):
    """Complete inventory report"""
    as_of_date: date
    rows: List[InventoryReportRow]


class BusinessSummaryLedger(BaseModel):
    """Business summary ledger (informational only)"""
    period: str = Field(..., description="e.g., 'Jan 2025' or 'FY 2024-25'")
    total_sales: float
    total_purchases: float
    total_output_gst: float
    total_input_gst: float
    net_gst_position: float = Field(..., description="Output GST - Input GST (informational)")


class GSTRReadyB2B(BaseModel):
    """GSTR-1 B2B invoice data"""
    invoice_number: str
    invoice_date: date
    customer_name: str
    customer_gstin: str
    taxable_value: float
    cgst: float
    sgst: float
    igst: float
    total_value: float


class GSTRReadyB2C(BaseModel):
    """GSTR-1 B2C invoice data"""
    invoice_date: date
    state_code: str
    taxable_value: float
    cgst: float
    sgst: float
    igst: float
    total_value: float


class GSTRReadyHSN(BaseModel):
    """GSTR-1 HSN summary"""
    hsn_code: str
    quantity: float
    unit: str
    taxable_value: float
    cgst_rate: int
    cgst: float
    sgst_rate: int
    sgst: float
    igst_rate: int
    igst: float
    total_value: float


class GSTRReadyResponse(BaseModel):
    """GSTR-1 ready export (preparation only)"""
    period: str
    b2b_invoices: List[GSTRReadyB2B]
    b2c_summary: List[GSTRReadyB2C]
    hsn_summary: List[GSTRReadyHSN]
    total_output_gst: float
    note: str = "Export only. Manual filing on gst.gov.in required."

class ReportFilters(BaseModel):
    """Common filters for all reports"""
    from_date: date
    to_date: date
    include_cancelled: bool = False
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None

    @field_validator('to_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if 'from_date' in info.data and v < info.data['from_date']:
            raise ValueError('to_date must be >= from_date')
        return v
