from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

class Unit(models.Model):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.name} ({self.short_name})"
    class Meta:
        ordering = ['name']

class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    mobile = models.CharField(max_length=15, blank=True, default='')
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    gstin = models.CharField(max_length=15, blank=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ['name']

class Vendor(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    mobile = models.CharField(max_length=15, blank=True, default='')
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    gstin = models.CharField(max_length=15, blank=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ['name']

class Product(models.Model):
    TAX_CHOICES = [
        (0, '0%'), (5, '5%'), (12, '12%'),
        (18, '18%'), (28, '28%'),
    ]
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    company = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.IntegerField(choices=TAX_CHOICES, default=18)
    hsn_code = models.CharField(max_length=20, blank=True)
    opening_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} ({self.code})"
    class Meta:
        ordering = ['name']

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('owner', 'Owner'),
        ('sales', 'Sales'),
        ('accounts', 'Accounts'),
        ('manager', 'Manager'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='sales')
    phone = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.user.username} ({self.role})"

class CompanyMaster(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    gstin = models.CharField(max_length=15, blank=True)
    pan = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class SalesmanMaster(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    area = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} ({self.code})"

class AreaMaster(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class GSTStateCode(models.Model):
    state_code = models.CharField(max_length=2, unique=True)
    state_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.state_code} - {self.state_name}"
    class Meta:
        ordering = ['state_code']

class GSTMaster(models.Model):
    GST_CHOICES = [(0,'0%'),(5,'5%'),(12,'12%'),(18,'18%'),(28,'28%')]
    hsn_code = models.CharField(max_length=20)
    description = models.CharField(max_length=200, blank=True)
    gst_rate = models.IntegerField(choices=GST_CHOICES, default=18)
    sale_ledger_5 = models.CharField(max_length=50, blank=True)
    sale_ledger_12 = models.CharField(max_length=50, blank=True)
    sale_ledger_18 = models.CharField(max_length=50, blank=True)
    sale_ledger_28 = models.CharField(max_length=50, blank=True)
    purchase_ledger_5 = models.CharField(max_length=50, blank=True)
    purchase_ledger_12 = models.CharField(max_length=50, blank=True)
    purchase_ledger_18 = models.CharField(max_length=50, blank=True)
    purchase_ledger_28 = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.hsn_code} - {self.gst_rate}%"

class GeneralLedgerMaster(models.Model):
    LEDGER_GROUPS = [
        ('PURCHASES', 'Purchases'),
        ('SALES', 'Sales'),
        ('EXPENSES_PAYABLE', 'Expenses Payable'),
        ('BANK', 'Bank Accounts'),
        ('CASH', 'Cash in Hand'),
        ('SUNDRY_DEBTOR', 'Sundry Debtors'),
        ('SUNDRY_CREDITOR', 'Sundry Creditors'),
        ('DUTIES_TAXES', 'Duties & Taxes'),
        ('FIXED_ASSETS', 'Fixed Assets'),
        ('CAPITAL', 'Capital Account'),
        ('OTHER', 'Other'),
    ]
    description = models.CharField(max_length=200, default='')
    ledger_code = models.CharField(max_length=20, unique=True, default='')
    ledger_group = models.CharField(max_length=30, choices=LEDGER_GROUPS, default='OTHER')
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.ledger_code} - {self.description}"
    class Meta:
        ordering = ['description']

class Party(models.Model):
    ACCOUNT_TYPE_CHOICES = [('SD', 'Sundry Debtor'), ('SC', 'Sundry Creditor')]
    GST_REG_CHOICES = [
        ('regular', 'Regular'), ('composition', 'Composition'),
        ('unregistered', 'Unregistered'), ('consumer', 'Consumer'),
        ('sez_unit', 'SEZ Unit'), ('sez_developer', 'SEZ Developer'),
        ('deemed_export', 'Deemed Export'), ('overseas', 'Overseas'),
        ('uin_holder', 'UIN Holder'),
    ]
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    mobile_number = models.CharField(max_length=15, blank=True)
    account_type = models.CharField(max_length=2, choices=ACCOUNT_TYPE_CHOICES, default='SD')
    gst_number = models.CharField(max_length=15, blank=True)
    gst_registration_type = models.CharField(max_length=20, choices=GST_REG_CHOICES, default='unregistered')
    state = models.ForeignKey(GSTStateCode, on_delete=models.SET_NULL, null=True, blank=True)
    gst_type = models.CharField(max_length=1, choices=[('I','Inter State'),('W','Within State')], default='W')
    amc_start_date = models.DateField(null=True, blank=True)
    amc_end_date = models.DateField(null=True, blank=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    legacy_customer_id = models.IntegerField(null=True, blank=True)
    legacy_vendor_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} ({self.code})"
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Parties"
