from django.db import models
from masters.models import Customer

class ServiceCall(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('inprogress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    call_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    call_date = models.DateField()
    issue_type = models.CharField(max_length=100)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    assigned_to = models.CharField(max_length=100, blank=True)
    resolution = models.TextField(blank=True)
    resolved_date = models.DateField(null=True, blank=True)
    charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.call_number} - {self.customer.name}"

    class Meta:
        ordering = ['-call_date']
