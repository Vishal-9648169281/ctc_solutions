from django.db import models
from masters.models import Customer

class Project(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('onetime', 'One-Time Payment'),
        ('amc', 'AMC (Annual)'),
        ('subscription', 'Monthly Subscription'),
    ]

    # Basic Info
    project_name = models.CharField(max_length=200)
    client = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    client_name_manual = models.CharField(max_length=200, blank=True, help_text="Use if client not in Customer master")
    technology = models.CharField(max_length=200, blank=True, help_text="e.g. Visual FoxPro, Django, PHP, .NET")
    description = models.TextField(blank=True)

    # Status (free text - fully customizable)
    status = models.CharField(max_length=100, default='Live', help_text="e.g. Live, Stopped, Under Development, On Hold")

    # Server / Hosting Details
    server_details = models.TextField(blank=True, help_text="Server IP, hosting provider, etc.")
    login_url = models.CharField(max_length=300, blank=True)
    login_username = models.CharField(max_length=100, blank=True)
    login_password = models.CharField(max_length=100, blank=True)

    # Payment Info
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='onetime')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="One-time amount / AMC amount / Monthly fee")

    # AMC Specific
    amc_start_date = models.DateField(null=True, blank=True)
    amc_end_date = models.DateField(null=True, blank=True)

    # Subscription Specific
    subscription_due_day = models.IntegerField(null=True, blank=True, help_text="Day of month payment is due (1-31)")

    # Payment Status
    last_payment_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    payment_status = models.CharField(max_length=50, default='Pending', help_text="e.g. Paid, Pending, Overdue")

    # Meta
    start_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.project_name

    @property
    def client_display(self):
        if self.client:
            return self.client.name
        return self.client_name_manual or "—"

    class Meta:
        ordering = ['-created_at']


class ProjectPayment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_mode = models.CharField(max_length=50, blank=True, help_text="Cash, Bank Transfer, UPI, Cheque")
    period_covered = models.CharField(max_length=100, blank=True, help_text="e.g. Jan 2026, FY 2025-26")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.project_name} - {self.payment_date}"

    class Meta:
        ordering = ['-payment_date']
