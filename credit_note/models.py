from django.db import models
from masters.models import Customer, Vendor, Product
from sales.models import SalesInvoice
from purchase.models import PurchaseBill

class CreditNote(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    TYPE_CHOICES = [
        ('customer', 'Customer Credit Note'),
        ('vendor', 'Vendor Debit Note'),
    ]
    note_number = models.CharField(max_length=50, unique=True)
    note_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='customer')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, null=True, blank=True)
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.SET_NULL, null=True, blank=True)
    bill = models.ForeignKey(PurchaseBill, on_delete=models.SET_NULL, null=True, blank=True)
    note_date = models.DateField()
    gr_number = models.CharField(max_length=50, blank=True)
    gr_date = models.DateField(null=True, blank=True)
    gst_bill_number = models.CharField(max_length=50, blank=True)
    gst_bill_date = models.DateField(null=True, blank=True)
    sector = models.CharField(max_length=100, blank=True)
    transport = models.CharField(max_length=100, blank=True)
    invoice_number_text = models.CharField(max_length=50, blank=True)
    invoice_date_text = models.DateField(null=True, blank=True)
    freight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_on_freight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dis_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_type = models.CharField(max_length=1, choices=[('I','Inter State'),('W','Within State')], default='W')
    reason = models.CharField(max_length=200, blank=True)
    add_less1_label = models.CharField(max_length=50, blank=True)
    add_less1 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    add_less2_label = models.CharField(max_length=50, blank=True)
    add_less2 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_rounded = models.IntegerField(default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.note_number}"

    class Meta:
        ordering = ['-note_date']


class CreditNoteItem(models.Model):
    note = models.ForeignKey(CreditNote, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    product_code = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=255, blank=True)
    hsn_no = models.CharField(max_length=20, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    mrp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amt = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.description or (self.product.name if self.product else '')} x {self.quantity}"
