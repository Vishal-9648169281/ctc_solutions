from django.db import models
from masters.models import Customer, Product

class SalesInvoice(models.Model):
    INVOICE_TYPES = [
        ('gst', 'GST Invoice'),
        ('proforma', 'Proforma'),
        ('export', 'Export Invoice'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
    ]
    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee'),
        ('USD', 'US Dollar'),
        ('CAD', 'Canadian Dollar'),
    ]
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPES, default='gst')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    invoice_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bill_discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_type = models.CharField(max_length=1, choices=[('W', 'Within State'), ('I', 'Inter State')], default='W')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    # GST Invoice Extra Fields
    reverse_charge = models.CharField(max_length=1, default='N')
    gr_number = models.CharField(max_length=50, blank=True)
    gr_date = models.DateField(null=True, blank=True)
    date_of_supply = models.DateField(null=True, blank=True)
    time_of_supply = models.TimeField(null=True, blank=True)
    place_of_supply = models.CharField(max_length=100, blank=True)
    order_number = models.CharField(max_length=50, blank=True)
    order_date = models.DateField(null=True, blank=True)
    vehicle_number = models.CharField(max_length=50, blank=True)
    transport = models.CharField(max_length=100, blank=True)
    despatched_to = models.CharField(max_length=200, blank=True)
    add_less1_label = models.CharField(max_length=50, blank=True)
    add_less1 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    add_less2_label = models.CharField(max_length=50, blank=True)
    add_less2 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_rounded = models.IntegerField(default=0)
    # Export Invoice Currency Fields
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    usd_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    cad_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cad = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_inr = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Export specific
    port_of_loading = models.CharField(max_length=100, blank=True)
    port_of_discharge = models.CharField(max_length=100, blank=True)
    country_of_destination = models.CharField(max_length=100, blank=True)
    shipping_bill_no = models.CharField(max_length=50, blank=True)
    lut_number = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"

    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount

    class Meta:
        ordering = ['-invoice_date']


class SalesInvoiceItem(models.Model):
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    hsn_no = models.CharField(max_length=20, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amt = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rate_usd = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    rate_cad = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_cad = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        name = self.product.name if self.product else self.description
        return f"{name} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.rate
        self.tax_amount = self.amount * self.tax_rate / 100
        if self.rate_usd:
            self.amount_usd = self.quantity * self.rate_usd
        if self.rate_cad:
            self.amount_cad = self.quantity * self.rate_cad
        super().save(*args, **kwargs)
