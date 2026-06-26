from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import CreditNote, CreditNoteItem
from masters.models import Customer, Vendor, Product
from sales.models import SalesInvoice
from purchase.models import PurchaseBill
import datetime

def generate_note_number(note_type):
    prefix = 'CN' if note_type == 'customer' else 'DN'
    last = CreditNote.objects.filter(note_type=note_type).order_by('-id').first()
    num = int(last.note_number.replace(prefix, '')) + 1 if last else 1
    return f"{prefix}{num:04d}"

@login_required
def note_list(request):
    note_type = request.GET.get('type', 'customer')
    notes = CreditNote.objects.filter(note_type=note_type)
    return render(request, 'credit_note/note_list.html', {
        'notes': notes,
        'note_type': note_type
    })

@login_required
def note_add(request):
    note_type = request.GET.get('type', 'customer')
    customers = Customer.objects.filter(is_active=True)
    vendors = Vendor.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    invoices = SalesInvoice.objects.all()
    bills = PurchaseBill.objects.all()
    if request.method == 'POST':
        note_type = request.POST.get('note_type', 'customer')
        try:
            with transaction.atomic():
                def _d(f):
                    v = request.POST.get(f, '').strip()
                    return v if v else None

                al1_label = request.POST.get('add_less1_label', '')
                al2_label = request.POST.get('add_less2_label', '')
                al1 = float(request.POST.get('add_less1', 0) or 0)
                al2 = float(request.POST.get('add_less2', 0) or 0)
                if al1_label.strip().upper().startswith('L'):
                    al1 = -abs(al1)
                if al2_label.strip().upper().startswith('L'):
                    al2 = -abs(al2)

                freight     = float(request.POST.get('freight', 0) or 0)
                gst_pct     = float(request.POST.get('gst_pct', 0) or 0)
                gst_on_frt  = float(request.POST.get('gst_on_freight_hidden', 0) or 0)
                dis_amount  = float(request.POST.get('dis_amount_hidden', 0) or 0)

                note = CreditNote.objects.create(
                    note_number=generate_note_number(note_type),
                    note_type=note_type,
                    customer_id=request.POST.get('customer') or None,
                    vendor_id=request.POST.get('vendor') or None,
                    invoice_id=request.POST.get('invoice') or None,
                    bill_id=request.POST.get('bill') or None,
                    note_date=request.POST['note_date'],
                    gr_number=request.POST.get('gr_number', ''),
                    gr_date=_d('gr_date'),
                    gst_bill_number=request.POST.get('gst_bill_number', ''),
                    gst_bill_date=_d('gst_bill_date'),
                    sector=request.POST.get('sector', ''),
                    transport=request.POST.get('transport', ''),
                    invoice_number_text=request.POST.get('invoice_number_text', ''),
                    invoice_date_text=_d('invoice_date_text'),
                    gst_type=request.POST.get('gst_type', 'W'),
                    reason=request.POST.get('reason', ''),
                    add_less1_label=al1_label,
                    add_less1=al1,
                    add_less2_label=al2_label,
                    add_less2=al2,
                    freight=freight,
                    gst_pct=gst_pct,
                    gst_on_freight=gst_on_frt,
                    dis_amount=dis_amount,
                    notes=request.POST.get('notes', ''),
                    subtotal=0, tax_amount=0, total_amount=0
                )
                import json as _json
                items_data = _json.loads(request.POST.get('items_json', '[]') or '[]')
                subtotal = 0
                tax_total = 0
                for item in items_data:
                    qty     = float(item.get('qty', 0))
                    rate    = float(item.get('rate', 0))
                    dis     = float(item.get('dis', 0))
                    srate   = float(item.get('sale_rate', rate))
                    tax     = float(item.get('tax_rate', 0))
                    amount  = float(item.get('amount', qty * srate))
                    tax_amt = float(item.get('tax_amt', amount * tax / 100))
                    CreditNoteItem.objects.create(
                        note=note,
                        product_code=item.get('product_code', ''),
                        description=item.get('description', ''),
                        hsn_no=item.get('hsn_no', ''),
                        unit=item.get('unit', ''),
                        quantity=qty,
                        mrp=float(item.get('mrp', 0)),
                        rate=rate,
                        discount_pct=dis,
                        discount_amt=float(item.get('dis_amt', 0)),
                        sale_rate=srate,
                        tax_rate=tax,
                        tax_amount=tax_amt,
                        amount=amount,
                    )
                    subtotal += amount
                    tax_total += tax_amt
                if note_type == 'vendor':
                    # Debit note: net = (subtotal - dis) + gst + freight + gst_on_freight
                    net = (subtotal - dis_amount) + tax_total + freight + gst_on_frt
                else:
                    net = subtotal + tax_total + al1 + al2
                note.subtotal = subtotal
                note.tax_amount = tax_total
                note.total_amount = net
                note.net_rounded = round(net)
                note.save()
                messages.success(request, f'Credit Note {note.note_number} created!')
                return redirect('note_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return render(request, 'credit_note/note_form.html', {
        'customers': customers,
        'vendors': vendors,
        'products': products,
        'invoices': invoices,
        'bills': bills,
        'note_type': note_type,
        'today': datetime.date.today(),
        'note_number': generate_note_number(note_type),
    })

@login_required
def note_detail(request, pk):
    note = get_object_or_404(CreditNote, pk=pk)
    items = note.items.select_related('product').all()
    return render(request, 'credit_note/note_detail.html', {'note': note, 'items': items})

@login_required
def note_delete(request, pk):
    note = get_object_or_404(CreditNote, pk=pk)
    note.delete()
    messages.success(request, 'Credit Note deleted!')
    return redirect('note_list')

@login_required
def note_approve(request, pk):
    note = get_object_or_404(CreditNote, pk=pk)
    note.status = 'approved'
    note.save()
    messages.success(request, f'Credit Note {note.note_number} approved!')
    return redirect('note_list')
