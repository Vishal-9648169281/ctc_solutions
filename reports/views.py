from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
import datetime
from sales.models import SalesInvoice
from purchase.models import PurchaseBill
from payments.models import ReceivePayment, PaymentReceipt
from masters.models import Customer, Vendor, Product
from service_call.models import ServiceCall

@login_required
def reports_home(request):
    return render(request, 'reports/reports_home.html')

@login_required
def sales_report(request):
    from_date = request.GET.get('from_date', str(datetime.date.today().replace(day=1)))
    to_date = request.GET.get('to_date', str(datetime.date.today()))
    invoices = SalesInvoice.objects.filter(
        invoice_date__gte=from_date,
        invoice_date__lte=to_date
    ).select_related('customer')
    total = invoices.aggregate(
        total_amount=Sum('total_amount'),
        total_paid=Sum('paid_amount')
    )
    return render(request, 'reports/sales_report.html', {
        'invoices': invoices,
        'from_date': from_date,
        'to_date': to_date,
        'total': total,
    })

@login_required
def purchase_report(request):
    from_date = request.GET.get('from_date', str(datetime.date.today().replace(day=1)))
    to_date = request.GET.get('to_date', str(datetime.date.today()))
    bills = PurchaseBill.objects.filter(
        bill_date__gte=from_date,
        bill_date__lte=to_date
    ).select_related('vendor')
    total = bills.aggregate(
        total_amount=Sum('total_amount'),
        total_paid=Sum('paid_amount')
    )
    return render(request, 'reports/purchase_report.html', {
        'bills': bills,
        'from_date': from_date,
        'to_date': to_date,
        'total': total,
    })

@login_required
def stock_report(request):
    products = Product.objects.filter(is_active=True).select_related('category', 'unit')
    low_stock = products.filter(current_stock__lte=0)
    return render(request, 'reports/stock_report.html', {
        'products': products,
        'low_stock_count': low_stock.count(),
    })

@login_required
def payment_report(request):
    from_date = request.GET.get('from_date', str(datetime.date.today().replace(day=1)))
    to_date = request.GET.get('to_date', str(datetime.date.today()))
    received = ReceivePayment.objects.filter(
        payment_date__gte=from_date,
        payment_date__lte=to_date
    ).select_related('customer')
    paid = PaymentReceipt.objects.filter(
        payment_date__gte=from_date,
        payment_date__lte=to_date
    ).select_related('vendor')
    total_received = received.aggregate(total=Sum('amount'))['total'] or 0
    total_paid = paid.aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'reports/payment_report.html', {
        'received': received,
        'paid': paid,
        'from_date': from_date,
        'to_date': to_date,
        'total_received': total_received,
        'total_paid': total_paid,
        'net': total_received - total_paid,
    })

@login_required
def service_report(request):
    from_date = request.GET.get('from_date', str(datetime.date.today().replace(day=1)))
    to_date = request.GET.get('to_date', str(datetime.date.today()))
    calls = ServiceCall.objects.filter(
        call_date__gte=from_date,
        call_date__lte=to_date
    ).select_related('customer')
    summary = calls.values('status').annotate(count=Count('id'))
    return render(request, 'reports/service_report.html', {
        'calls': calls,
        'from_date': from_date,
        'to_date': to_date,
        'summary': summary,
    })
