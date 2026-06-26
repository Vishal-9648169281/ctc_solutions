from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ReceivePayment, PaymentReceipt
from masters.models import Customer, Vendor
from sales.models import SalesInvoice
from purchase.models import PurchaseBill
import datetime

def generate_receipt_number():
    last = ReceivePayment.objects.order_by('-id').first()
    num = int(last.receipt_number.replace('RCP', '')) + 1 if last else 1
    return f"RCP{num:04d}"

def generate_voucher_number():
    last = PaymentReceipt.objects.order_by('-id').first()
    num = int(last.voucher_number.replace('PMT', '')) + 1 if last else 1
    return f"PMT{num:04d}"

# ─── RECEIVE PAYMENT (from customers) ───────────────────
@login_required
def receive_list(request):
    payments = ReceivePayment.objects.select_related('customer').all()
    return render(request, 'payments/receive_list.html', {'payments': payments})

@login_required
def receive_add(request):
    customers = Customer.objects.filter(is_active=True)
    invoices = SalesInvoice.objects.filter(status__in=['pending', 'partial'])
    if request.method == 'POST':
        customer_id = request.POST['customer']
        invoice_id = request.POST.get('invoice') or None
        amount = float(request.POST['amount'])
        payment = ReceivePayment.objects.create(
            receipt_number=generate_receipt_number(),
            customer_id=customer_id,
            invoice_id=invoice_id,
            payment_date=request.POST['payment_date'],
            amount=amount,
            payment_mode=request.POST['payment_mode'],
            reference_number=request.POST.get('reference_number', ''),
            notes=request.POST.get('notes', ''),
        )
        if invoice_id:
            invoice = SalesInvoice.objects.get(pk=invoice_id)
            invoice.paid_amount += amount
            if invoice.paid_amount >= invoice.total_amount:
                invoice.status = 'paid'
            else:
                invoice.status = 'partial'
            invoice.save()
        messages.success(request, f'Payment {payment.receipt_number} received!')
        return redirect('receive_list')
    return render(request, 'payments/receive_form.html', {
        'customers': customers,
        'invoices': invoices,
        'today': datetime.date.today(),
        'receipt_number': generate_receipt_number(),
    })

# ─── PAYMENT RECEIPT (to vendors) ───────────────────────
@login_required
def receipt_list(request):
    payments = PaymentReceipt.objects.select_related('vendor').all()
    return render(request, 'payments/receipt_list.html', {'payments': payments})

@login_required
def receipt_add(request):
    vendors = Vendor.objects.filter(is_active=True)
    bills = PurchaseBill.objects.filter(status__in=['pending', 'partial'])
    if request.method == 'POST':
        vendor_id = request.POST['vendor']
        bill_id = request.POST.get('bill') or None
        amount = float(request.POST['amount'])
        payment = PaymentReceipt.objects.create(
            voucher_number=generate_voucher_number(),
            vendor_id=vendor_id,
            bill_id=bill_id,
            payment_date=request.POST['payment_date'],
            amount=amount,
            payment_mode=request.POST['payment_mode'],
            reference_number=request.POST.get('reference_number', ''),
            notes=request.POST.get('notes', ''),
        )
        if bill_id:
            bill = PurchaseBill.objects.get(pk=bill_id)
            bill.paid_amount += amount
            if bill.paid_amount >= bill.total_amount:
                bill.status = 'paid'
            else:
                bill.status = 'partial'
            bill.save()
        messages.success(request, f'Payment {payment.voucher_number} made!')
        return redirect('receipt_list')
    return render(request, 'payments/receipt_form.html', {
        'vendors': vendors,
        'bills': bills,
        'today': datetime.date.today(),
        'voucher_number': generate_voucher_number(),
    })
