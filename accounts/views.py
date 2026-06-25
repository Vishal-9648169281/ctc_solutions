from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from sales.models import SalesInvoice
from purchase.models import PurchaseBill
from payments.models import ReceivePayment, PaymentReceipt
from masters.models import Customer, Vendor

@login_required
def accounts_home(request):
    total_sales = SalesInvoice.objects.aggregate(t=Sum('total_amount'))['t'] or 0
    total_purchase = PurchaseBill.objects.aggregate(t=Sum('total_amount'))['t'] or 0
    total_received = ReceivePayment.objects.aggregate(t=Sum('amount'))['t'] or 0
    total_paid = PaymentReceipt.objects.aggregate(t=Sum('amount'))['t'] or 0
    receivable = SalesInvoice.objects.filter(status__in=['pending','partial']).aggregate(t=Sum('total_amount'))['t'] or 0
    payable = PurchaseBill.objects.filter(status__in=['pending','partial']).aggregate(t=Sum('total_amount'))['t'] or 0
    context = {
        'total_sales': total_sales,
        'total_purchase': total_purchase,
        'total_received': total_received,
        'total_paid': total_paid,
        'receivable': receivable,
        'payable': payable,
        'profit': total_sales - total_purchase,
    }
    return render(request, 'accounts/accounts_home.html', context)

@login_required
def customer_ledger(request):
    customer_id = request.GET.get('customer', '')
    customers = Customer.objects.filter(is_active=True)
    invoices = []
    payments = []
    customer = None
    total_invoice = 0
    total_paid = 0
    if customer_id:
        from masters.models import Customer as C
        customer = C.objects.get(pk=customer_id)
        invoices = SalesInvoice.objects.filter(customer_id=customer_id).order_by('invoice_date')
        payments = ReceivePayment.objects.filter(customer_id=customer_id).order_by('payment_date')
        total_invoice = invoices.aggregate(t=Sum('total_amount'))['t'] or 0
        total_paid = payments.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'accounts/customer_ledger.html', {
        'customers': customers,
        'customer': customer,
        'invoices': invoices,
        'payments': payments,
        'total_invoice': total_invoice,
        'total_paid': total_paid,
        'balance': total_invoice - total_paid,
        'selected_customer': customer_id,
    })

@login_required
def vendor_ledger(request):
    vendor_id = request.GET.get('vendor', '')
    vendors = Vendor.objects.filter(is_active=True)
    bills = []
    payments = []
    vendor = None
    total_bill = 0
    total_paid = 0
    if vendor_id:
        from masters.models import Vendor as V
        vendor = V.objects.get(pk=vendor_id)
        bills = PurchaseBill.objects.filter(vendor_id=vendor_id).order_by('bill_date')
        payments = PaymentReceipt.objects.filter(vendor_id=vendor_id).order_by('payment_date')
        total_bill = bills.aggregate(t=Sum('total_amount'))['t'] or 0
        total_paid = payments.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'accounts/vendor_ledger.html', {
        'vendors': vendors,
        'vendor': vendor,
        'bills': bills,
        'payments': payments,
        'total_bill': total_bill,
        'total_paid': total_paid,
        'balance': total_bill - total_paid,
        'selected_vendor': vendor_id,
    })
