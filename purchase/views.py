from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import PurchaseBill, PurchaseBillItem
from masters.models import Vendor, Product
import datetime

def generate_bill_number():
    last = PurchaseBill.objects.order_by('-id').first()
    if last:
        num = int(last.bill_number.replace('PB', '')) + 1
    else:
        num = 1
    return f"PB{num:04d}"

@login_required
def bill_list(request):
    bills = PurchaseBill.objects.select_related('vendor').all()
    return render(request, 'purchase/bill_list.html', {'bills': bills})

@login_required
def bill_add(request):
    vendors = Vendor.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                bill = PurchaseBill.objects.create(
                    bill_number=generate_bill_number(),
                    vendor_id=request.POST['vendor'],
                    bill_date=request.POST['bill_date'],
                    due_date=request.POST.get('due_date') or None,
                    notes=request.POST.get('notes', ''),
                    subtotal=0, tax_amount=0, total_amount=0
                )
                import json
                items_data = json.loads(request.POST.get('items_json', '[]'))
                subtotal = 0
                tax_total = 0
                dis_total = 0
                for item in items_data:
                    if item.get('product_id'):
                        qty = float(item.get('qty', 0))
                        rate = float(item.get('rate', 0))
                        dis_pct = float(item.get('dis', 0))
                        tax = float(item.get('tax', 0))
                        gross_amt = qty * rate
                        dis_amt = gross_amt * dis_pct / 100
                        after_dis = gross_amt - dis_amt
                        tax_amt = after_dis * tax / 100
                        amount = after_dis
                        PurchaseBillItem.objects.create(
                            bill=bill,
                            product_id=item['product_id'],
                            quantity=qty,
                            rate=rate,
                            tax_rate=tax,
                            tax_amount=tax_amt,
                            amount=amount
                        )
                        product = Product.objects.get(pk=item['product_id'])
                        product.current_stock += qty
                        product.save()
                        subtotal += gross_amt
                        dis_total += dis_amt
                        tax_total += tax_amt
                discount = float(request.POST.get('discount', 0))
                bill.subtotal = subtotal
                bill.tax_amount = tax_total
                bill.discount = discount
                bill.total_amount = subtotal - dis_total + tax_total - discount
                bill.save()
                messages.success(request, f'Purchase Bill {bill.bill_number} created!')
                return redirect('bill_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    context = {
        'vendors': vendors,
        'products': products,
        'today': datetime.date.today(),
        'bill_number': generate_bill_number(),
    }
    return render(request, 'purchase/bill_form.html', context)

@login_required
def bill_detail(request, pk):
    bill = get_object_or_404(PurchaseBill, pk=pk)
    items = bill.items.select_related('product').all()
    return render(request, 'purchase/bill_detail.html', {'bill': bill, 'items': items})

@login_required
def bill_delete(request, pk):
    bill = get_object_or_404(PurchaseBill, pk=pk)
    for item in bill.items.all():
        item.product.current_stock -= item.quantity
        item.product.save()
    bill.delete()
    messages.success(request, 'Purchase bill deleted!')
    return redirect('bill_list')


