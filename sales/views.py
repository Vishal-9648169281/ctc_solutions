from decimal import Decimal
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import SalesInvoice, SalesInvoiceItem
from masters.models import Customer, Product
import datetime
import traceback

def generate_invoice_number(invoice_type):
    prefix = {"gst": "GST", "proforma": "PRO", "export": "EXP"}.get(invoice_type, "INV")
    candidates = SalesInvoice.objects.filter(invoice_type=invoice_type).order_by("-id")
    num = 1
    for c in candidates:
        try:
            num = int(c.invoice_number.replace(prefix, "")) + 1
            break
        except (ValueError, AttributeError):
            continue
    return f"{prefix}{num:04d}"

@login_required
def invoice_list(request):
    invoice_type = request.GET.get("type", "all")
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    query = request.GET.get('q', '')
    if invoice_type == "all":
        invoices = SalesInvoice.objects.all().select_related("customer").order_by("-invoice_date")
    else:
        invoices = SalesInvoice.objects.filter(invoice_type=invoice_type).select_related("customer").order_by("-invoice_date")
    if from_date:
        invoices = invoices.filter(invoice_date__gte=from_date)
    if to_date:
        invoices = invoices.filter(invoice_date__lte=to_date)
    if query:
        invoices = invoices.filter(customer__name__icontains=query)
    return render(request, "sales/invoice_list.html", {
        "invoices": invoices,
        "invoice_type": invoice_type,
        "current_type": invoice_type,
        "from_date": from_date,
        "to_date": to_date,
        "query": query,
    })

@login_required
def invoice_add(request):
    invoice_type = request.GET.get("type", "gst")
    customers = Customer.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    if request.method == "POST":
        invoice_type = request.POST.get("invoice_type", "gst")
        try:
            with transaction.atomic():
                def _date(key):
                    v = request.POST.get(key, '').strip()
                    return v if v else None
                def _time(key):
                    v = request.POST.get(key, '').strip()
                    return v if v else None

                invoice = SalesInvoice.objects.create(
                    invoice_number=generate_invoice_number(invoice_type),
                    invoice_type=invoice_type,
                    customer_id=request.POST["customer"],
                    invoice_date=request.POST["invoice_date"],
                    due_date=_date("due_date"),
                    notes=request.POST.get("notes", ""),
                    reverse_charge=request.POST.get("reverse_charge", "N"),
                    gst_type=request.POST.get("gst_type", "W"),
                    gr_number=request.POST.get("gr_number", ""),
                    gr_date=_date("gr_date"),
                    date_of_supply=_date("date_of_supply"),
                    time_of_supply=_time("time_of_supply"),
                    place_of_supply=request.POST.get("place_of_supply", ""),
                    order_number=request.POST.get("order_number", ""),
                    order_date=_date("order_date"),
                    vehicle_number=request.POST.get("vehicle_number", ""),
                    transport=request.POST.get("transport", ""),
                    despatched_to=request.POST.get("despatched_to", ""),
                    add_less1_label=request.POST.get("add_less1_label", ""),
                    add_less1=Decimal(str(request.POST.get("add_less1", 0) or 0)),
                    add_less2_label=request.POST.get("add_less2_label", ""),
                    add_less2=Decimal(str(request.POST.get("add_less2", 0) or 0)),
                    bill_discount_pct=Decimal(str(request.POST.get("bill_discount_pct", 0) or 0)),
                    subtotal=0, tax_amount=0, total_amount=0
                )
                product_ids = request.POST.getlist("product[]")
                descriptions = request.POST.getlist("description[]")
                quantities = request.POST.getlist("quantity[]")
                rates = request.POST.getlist("rate[]")
                tax_rates = request.POST.getlist("tax_rate[]")
                hsn_nos = request.POST.getlist("hsn_no[]")
                units = request.POST.getlist("unit[]")
                discount_pcts = request.POST.getlist("discount_pct[]")
                subtotal = 0
                tax_total = 0
                for i in range(len(quantities)):
                    pid = product_ids[i] if i < len(product_ids) else ''
                    desc = descriptions[i].strip() if i < len(descriptions) else ''
                    if not pid and not desc:
                        continue
                    qty = float(quantities[i] or 0)
                    rate = float(rates[i] or 0)
                    tax = float(tax_rates[i] or 0)
                    dis_pct = float(discount_pcts[i] if i < len(discount_pcts) else 0 or 0)
                    dis_amt = rate * qty * dis_pct / 100
                    amount = qty * rate - dis_amt
                    tax_amt = amount * tax / 100
                    SalesInvoiceItem.objects.create(
                        invoice=invoice,
                        product_id=pid if pid else None,
                        description=desc,
                        hsn_no=hsn_nos[i] if i < len(hsn_nos) else '',
                        unit=units[i] if i < len(units) else '',
                        quantity=qty,
                        rate=rate,
                        discount_pct=Decimal(str(dis_pct)),
                        discount_amt=Decimal(str(round(dis_amt, 2))),
                        tax_rate=tax,
                        tax_amount=tax_amt,
                        amount=amount
                    )
                    if pid:
                        product = Product.objects.get(pk=pid)
                        product.current_stock -= Decimal(str(qty))
                        product.save()
                    subtotal += amount
                    tax_total += tax_amt
                discount = float(request.POST.get("discount", 0) or 0)
                bill_discount_pct = float(request.POST.get("bill_discount_pct", 0) or 0)
                bill_discount_amt = (subtotal + tax_total) * bill_discount_pct / 100
                al1_label = request.POST.get("add_less1_label", "")
                al2_label = request.POST.get("add_less2_label", "")
                add_less1 = float(request.POST.get("add_less1", 0) or 0)
                add_less2 = float(request.POST.get("add_less2", 0) or 0)
                # Auto-negate if label starts with L (Less)
                if al1_label and al1_label.strip().upper().startswith('L'):
                    add_less1 = -abs(add_less1)
                if al2_label and al2_label.strip().upper().startswith('L'):
                    add_less2 = -abs(add_less2)
                net = subtotal + tax_total + add_less1 + add_less2 - discount - bill_discount_amt
                invoice.subtotal = subtotal
                invoice.tax_amount = tax_total
                invoice.discount = discount
                invoice.bill_discount_pct = Decimal(str(bill_discount_pct))
                invoice.total_amount = net
                invoice.net_rounded = round(net)
                invoice.save()
                messages.success(request, f"Invoice {invoice.invoice_number} created successfully!")
                return redirect(f"/sales/invoices/{invoice.pk}/?new=1")
        except Exception as e:
            error_msg = traceback.format_exc()
            print("INVOICE SAVE ERROR:", error_msg)
            messages.error(request, f"Error saving invoice: {str(e)}")
    context = {
        "customers": customers,
        "products": products,
        "today": datetime.date.today().strftime("%Y-%m-%d"),
        "invoice_type": invoice_type,
        "invoice_number": generate_invoice_number(invoice_type),
    }
    return render(request, "sales/invoice_form.html", context)

@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(SalesInvoice, pk=pk)
    items = invoice.items.select_related("product").all()
    new_invoice = request.GET.get("new", False)
    return render(request, "sales/invoice_detail.html", {
        "invoice": invoice,
        "items": items,
        "new_invoice": new_invoice,
    })

@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(SalesInvoice, pk=pk)
    for item in invoice.items.all():
        item.product.current_stock += Decimal(str(item.quantity))
        item.product.save()
    invoice.delete()
    messages.success(request, "Invoice deleted!")
    return redirect("invoice_list")

@login_required
def invoice_pdf(request, pk):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.graphics.shapes import Drawing, Line
    try:
        from num2words import num2words as n2w
        has_n2w = True
    except:
        has_n2w = False

    invoice = get_object_or_404(SalesInvoice, pk=pk)
    items = invoice.items.select_related("product").all()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=Invoice_{invoice.invoice_number}.pdf"

    doc = SimpleDocTemplate(
        response, pagesize=A4,
        rightMargin=8*mm, leftMargin=8*mm,
        topMargin=6*mm, bottomMargin=6*mm
    )
    elements = []
    W = 194*mm

    def ps(name, sz=9, bold=False, align=TA_LEFT, color=colors.black, leading=None):
        return ParagraphStyle(
            name, fontSize=sz,
            fontName="Helvetica-Bold" if bold else "Helvetica",
            alignment=align, textColor=color,
            leading=leading or (sz + 3)
        )

    BLUE = colors.HexColor("#1a237e")
    LBLUE = colors.HexColor("#e8eaf6")
    GREY = colors.HexColor("#666666")



    # ── TAX INVOICE TITLE ────────────────────────────────
    title_row = Table([[
        Paragraph("TAX INVOICE", ps("ti", 13, bold=True, align=TA_CENTER, color=BLUE)),
        Paragraph("Original For Buyer", ps("ofb", 8, align=TA_RIGHT, color=GREY))
    ]], colWidths=[140*mm, 54*mm])
    title_row.setStyle(TableStyle([("PADDING", (0,0), (-1,-1), 2)]))
    elements.append(title_row)
    elements.append(HRFlowable(width=W, thickness=1, color=BLUE, spaceAfter=3))

    # ── COMPANY BILL TOP LOGO (full width) ───────────────
    import os
    logo_path = os.path.join(settings.BASE_DIR, "company_bill_top_logo.png")
    if os.path.exists(logo_path):
        from reportlab.platypus import Image as RLImage
        from PIL import Image as PILImage
        with PILImage.open(logo_path) as im:
            orig_w, orig_h = im.size
        aspect = orig_h / float(orig_w)
        logo_img = RLImage(logo_path, width=W, height=W*aspect)
        elements.append(logo_img)
        elements.append(Spacer(1, 2*mm))

    # ── GSTIN & INVOICE INFO ─────────────────────────────
    inv_date = invoice.invoice_date.strftime("%d-%m-%Y") if hasattr(invoice.invoice_date, "strftime") else str(invoice.invoice_date)
    info = Table([
        [Paragraph("G.S.T.IN No.: <b>04ALVPK9235D1ZW</b>", ps("i1", 8)),
         Paragraph("Transportation Mode :", ps("i2", 8)),
         Paragraph("UDYAM REG. NO.: UDYAM-CH-09-0060963", ps("i3", 8))],
        [Paragraph(f"Tax is Payable on Reverse Charge(Yes/No): <b>{'Yes' if invoice.reverse_charge == 'Y' else 'No'}</b>", ps("i4", 8)),
         Paragraph(f"Veh. No : {invoice.vehicle_number or ''}", ps("i5", 8)),
         Paragraph("", ps("i6", 8))],
        [Paragraph(f"Invoice Serial Number : <b>{invoice.invoice_number}</b>", ps("i7", 8, bold=True)),
         Paragraph("Date &amp; Time of Supply : -", ps("i8", 8)),
         Paragraph("", ps("i9", 8))],
        [Paragraph(f"Invoice Date : <b>{inv_date}</b>", ps("i10", 8, bold=True)),
         Paragraph(f"Place Of Supply : {invoice.place_of_supply or ''}", ps("i11", 8)),
         Paragraph("", ps("i12", 8))],
    ], colWidths=[80*mm, 64*mm, 50*mm])
    info.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.black),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("PADDING", (0,0), (-1,-1), 3),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    elements.append(info)
    elements.append(Spacer(1, 2*mm))

    # ── BILL TO ──────────────────────────────────────────
    party = Table([
        [Paragraph("<b>Details of Receiver (Billed to)</b>", ps("pb1", 8, bold=True)),
         Paragraph("<b>Details of Consignee (Shipped to)</b>", ps("pb2", 8, bold=True))],
        [Paragraph(f"Name: <b>{invoice.customer.name}</b>", ps("p1", 8)),
         Paragraph("Name:", ps("p2", 8))],
        [Paragraph(f"Address: {invoice.customer.address or ''}", ps("p3", 8)),
         Paragraph("Address:", ps("p4", 8))],
        [Paragraph(f"State: {invoice.customer.state or ''} &nbsp;&nbsp; State Code:", ps("p5", 8)),
         Paragraph("State: &nbsp;&nbsp; State Code:", ps("p6", 8))],
        [Paragraph(f"GSTIN Number: {invoice.customer.gstin or ''}", ps("p7", 8)),
         Paragraph("GSTIN Number:", ps("p8", 8))],
    ], colWidths=[97*mm, 97*mm])
    party.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.black),
        ("LINEAFTER", (0,0), (0,-1), 0.5, colors.black),
        ("BACKGROUND", (0,0), (-1,0), LBLUE),
        ("PADDING", (0,0), (-1,-1), 3),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    elements.append(party)
    elements.append(Spacer(1, 2*mm))

    # ── ORDER INFO ───────────────────────────────────────
    gr_date_str = invoice.gr_date.strftime("%d-%m-%Y") if invoice.gr_date else "-"
    order_date_str = invoice.order_date.strftime("%d-%m-%Y") if invoice.order_date else "-"
    order = Table([
        [Paragraph(f"ORDER NO. : {invoice.order_number or ''}", ps("o1", 8)),
         Paragraph(f"G.R.NO. : {invoice.gr_number or ''}", ps("o2", 8))],
        [Paragraph(f"ORDER DATE : {order_date_str}", ps("o3", 8)),
         Paragraph(f"G.R DATE : {gr_date_str}", ps("o4", 8))],
    ], colWidths=[97*mm, 97*mm])
    order.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.black),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("PADDING", (0,0), (-1,-1), 3),
    ]))
    elements.append(order)
    elements.append(Spacer(1, 2*mm))

    # ── ITEMS TABLE ──────────────────────────────────────
    col_w = [8*mm, 38*mm, 15*mm, 10*mm, 10*mm, 16*mm, 18*mm, 24*mm, 18*mm, 18*mm, 19*mm]
    rows = [[
        Paragraph("<b>S.\nNO</b>", ps("h0", 7, bold=True, align=TA_CENTER)),
        Paragraph("<b>Description of Goods</b>", ps("h1", 7, bold=True, align=TA_CENTER)),
        Paragraph("<b>HSN Code\n/ SAC</b>", ps("h2", 7, bold=True, align=TA_CENTER)),
        Paragraph("<b>Qty</b>", ps("h3", 7, bold=True, align=TA_CENTER)),
        Paragraph("<b>UOM</b>", ps("h4", 7, bold=True, align=TA_CENTER)),
        Paragraph("<b>Rate</b>", ps("h5", 7, bold=True, align=TA_CENTER)),
        Paragraph("<b>Taxable\nValue</b>", ps("h6", 7, bold=True, align=TA_CENTER)),
        Paragraph("<b>CGST\nRate   Amount</b>", ps("h7", 7, bold=True, align=TA_CENTER)),
        Paragraph("<b>UTGST\nRate   Amount</b>", ps("h8", 7, bold=True, align=TA_CENTER)),
        Paragraph("<b>IGST\nRate   Amount</b>", ps("h9", 7, bold=True, align=TA_CENTER)),
        Paragraph("<b>Amount</b>", ps("h10", 7, bold=True, align=TA_CENTER)),
    ]]

    total_taxable = 0
    total_cgst = 0
    total_amt = 0

    for idx, item in enumerate(items, 1):
        taxable = float(item.quantity) * float(item.rate)
        cgst_rate = float(item.tax_rate) / 2
        cgst_amt = taxable * cgst_rate / 100
        amt = taxable + (cgst_amt * 2)
        total_taxable += taxable
        total_cgst += cgst_amt
        total_amt += amt
        unit_name = item.unit or (str(item.product.unit) if item.product and item.product.unit else "NOS")
        hsn_display = item.hsn_no or (item.product.hsn_code if item.product else "") or ""
        item_name = item.description or (item.product.name if item.product else "")
        rows.append([
            Paragraph(str(idx), ps(f"r0{idx}", 7, align=TA_CENTER)),
            Paragraph(item_name, ps(f"r1{idx}", 7)),
            Paragraph(hsn_display, ps(f"r2{idx}", 7, align=TA_CENTER)),
            Paragraph(str(item.quantity), ps(f"r3{idx}", 7, align=TA_CENTER)),
            Paragraph(unit_name, ps(f"r4{idx}", 7, align=TA_CENTER)),
            Paragraph(f"{float(item.rate):.2f}", ps(f"r5{idx}", 7, align=TA_RIGHT)),
            Paragraph(f"{taxable:.2f}", ps(f"r6{idx}", 7, align=TA_RIGHT)),
            Paragraph(f"{cgst_rate:.0f}%   {cgst_amt:.2f}", ps(f"r7{idx}", 7, align=TA_RIGHT)),
            Paragraph(f"0.00   0.00", ps(f"r8{idx}", 7, align=TA_RIGHT)),
            Paragraph(f"0.00   0.00", ps(f"r9{idx}", 7, align=TA_RIGHT)),
            Paragraph(f"{amt:.2f}", ps(f"r10{idx}", 7, align=TA_RIGHT)),
        ])

    # Add empty rows
    for _ in range(max(0, 6 - len(items))):
        rows.append([Paragraph("", ps("e", 7))] * 11)

    item_t = Table(rows, colWidths=col_w)
    item_t.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.black),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), LBLUE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 7),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("PADDING", (0,0), (-1,-1), 2),
    ]))
    elements.append(item_t)
    elements.append(Spacer(1, 2*mm))

    # ── AMOUNT IN WORDS ──────────────────────────────────
    curr = invoice.currency or 'INR'
    curr_symbol = {'INR': 'Rs.', 'USD': 'USD $', 'CAD': 'CAD $'}.get(curr, 'Rs.')
    usd_rate = float(invoice.usd_rate or 0)
    cad_rate = float(invoice.cad_rate or 0)
    total_inr = float(invoice.total_amount or 0)
    total_usd = float(invoice.total_usd or 0) or (total_inr / usd_rate if usd_rate else 0)
    total_cad = float(invoice.total_cad or 0) or (total_inr / cad_rate if cad_rate else 0)

    try:
        if has_n2w:
            words = curr_symbol + n2w(int(invoice.total_amount), lang="en_IN").title() + " Only"
        else:
            words = f"{curr_symbol}{invoice.total_amount:.2f} Only"
    except:
        words = f"{curr_symbol}{invoice.total_amount:.2f} Only"

    words_t = Table([[
        Paragraph(f"Invoice Value (In Words): <b>{words}</b>", ps("w1", 8)),
        Paragraph(f"<b>Rs. {total_inr:.2f}</b>",
            ps("w2", 9, bold=True, align=TA_RIGHT)),
    ]], colWidths=[134*mm, 60*mm])
    words_t.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.black),
        ("LINEAFTER", (0,0), (0,0), 0.5, colors.black),
        ("PADDING", (0,0), (-1,-1), 4),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    elements.append(words_t)
    elements.append(Spacer(1, 2*mm))

    # ── REMARKS & TOTALS ─────────────────────────────────
    rem_t = Table([
        [Paragraph("<b>REMARKS:</b>", ps("rm1", 8, bold=True)),
         Paragraph("Total Amount Before Tax", ps("t1", 8)),
         Paragraph(f"Rs. {total_taxable:.2f}", ps("a1", 8, align=TA_RIGHT))],
        [Paragraph(invoice.notes or "", ps("rm2", 8)),
         Paragraph("ADD: CGST", ps("t2", 8)),
         Paragraph(f"Rs. {total_cgst:.2f}", ps("a2", 8, align=TA_RIGHT))],
        [Paragraph("", ps("rm3", 8)),
         Paragraph("ADD: UTGST", ps("t3", 8)),
         Paragraph("Rs. 0.00", ps("a3", 8, align=TA_RIGHT))],
        [Paragraph("", ps("rm4", 8)),
         Paragraph("ADD: GST", ps("t4", 8)),
         Paragraph(f"Rs. {total_cgst:.2f}", ps("a4", 8, align=TA_RIGHT))],
        [Paragraph("", ps("rm5", 8)),
         Paragraph("<b>Tax Amount - GST</b>", ps("t5", 8, bold=True)),
         Paragraph(f"<b>Rs. {float(invoice.tax_amount):.2f}</b>",
             ps("a5", 8, bold=True, align=TA_RIGHT))],
        [Paragraph("", ps("rm6", 8)),
         Paragraph("<b>Total Amount After Tax</b>", ps("t6", 8, bold=True)),
         Paragraph(f"<b>Rs. {total_inr:.2f}</b>",
             ps("a6", 9, bold=True, align=TA_RIGHT))],
        *([
            [Paragraph("", ps("rm7", 8)),
             Paragraph(f"Exchange Rate (1 USD = Rs. {usd_rate:.2f})", ps("t7", 8)),
             Paragraph(f"USD $ {total_usd:.2f}", ps("a7", 8, bold=True, align=TA_RIGHT))],
        ] if curr == 'USD' and usd_rate else []),
        *([
            [Paragraph("", ps("rm8", 8)),
             Paragraph(f"Exchange Rate (1 CAD = Rs. {cad_rate:.2f})", ps("t8", 8)),
             Paragraph(f"CAD $ {total_cad:.2f}", ps("a8", 8, bold=True, align=TA_RIGHT))],
        ] if curr == 'CAD' and cad_rate else []),
    ], colWidths=[65*mm, 89*mm, 40*mm])
    rem_t.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.black),
        ("LINEAFTER", (0,0), (0,-1), 0.5, colors.black),
        ("LINEBEFORE", (2,0), (2,-1), 0.5, colors.black),
        ("BACKGROUND", (1,5), (2,5), LBLUE),
        ("PADDING", (0,0), (-1,-1), 3),
        ("SPAN", (0,1), (0,-1)),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    elements.append(rem_t)
    elements.append(Spacer(1, 2*mm))

    # ── CERTIFIED TEXT ───────────────────────────────────
    elements.append(Paragraph(
        "Certified that the Particulars given above are true and correct",
        ps("cert", 7, color=GREY)))
    elements.append(Spacer(1, 2*mm))

    # ── BANK & TERMS & SIGNATURE ─────────────────────────
    bank_t = Table([[
        Paragraph(
            "<b>BANK NAME : ICICI BANK</b><br/>"
            "A/c No &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: 632205005712<br/>"
            "BRANCH &nbsp;&nbsp;&nbsp;&nbsp;: SECTOR 33C<br/>"
            "IF SC CODE : ICIC0000322",
            ps("bk", 8)),
        Paragraph(
            "<b>TERM &amp; CONDITION</b><br/>"
            "1. Our responsibility ceases as soon as the goods are "
            "handed over to Carrier/customer.<br/>"
            "2. All Disputes subject to Chandigarh Jurisdiction.<br/>"
            "3. Interest @ Rs.2+% p.a. will be charged on all amounts "
            "remained unpaid after 15 days.",
            ps("tc", 7)),
        Paragraph(
            "<b>For CHANDIGARH TEAM COMPUTERS</b>"
            "<br/><br/><br/><br/><br/>"
            "Authorised Signatory",
            ps("sg", 8, align=TA_CENTER)),
    ]], colWidths=[55*mm, 86*mm, 53*mm])
    bank_t.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.black),
        ("LINEAFTER", (0,0), (0,0), 0.5, colors.black),
        ("LINEAFTER", (1,0), (1,0), 0.5, colors.black),
        ("PADDING", (0,0), (-1,-1), 5),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    elements.append(bank_t)

    doc.build(elements)
    return response






@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(SalesInvoice, pk=pk)
    from masters.models import Customer, Product
    customers = Customer.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_active=True).order_by('name')
    invoice_type = invoice.invoice_type
    prefix_map = {"gst": "GST", "proforma": "PRO", "export": "EXP"}
    prefix = prefix_map.get(invoice_type, "INV")

    if request.method == 'POST':
        try:
            import json
            from decimal import Decimal
            invoice.customer_id = request.POST.get('customer')
            invoice.invoice_date = request.POST.get('invoice_date')
            invoice.due_date = request.POST.get('due_date') or None
            invoice.notes = request.POST.get('notes', '')

            # Delete old items and restore stock
            for old_item in invoice.items.all():
                old_item.product.current_stock += Decimal(str(old_item.quantity))
                old_item.product.save()
            invoice.items.all().delete()

            # Re-add items
            items_json = request.POST.get('items_json', '[]')
            items = json.loads(items_json)
            subtotal = Decimal('0')
            tax_total = Decimal('0')
            for item in items:
                if item.get('product_id'):
                    qty = Decimal(str(item['qty']))
                    rate = Decimal(str(item['rate']))
                    tax_rate = Decimal(str(item.get('tax_rate', 0)))
                    amount = qty * rate
                    tax_amt = amount * tax_rate / 100
                    from sales.models import SalesInvoiceItem
                    SalesInvoiceItem.objects.create(
                        invoice=invoice,
                        product_id=item['product_id'],
                        quantity=qty,
                        rate=rate,
                        tax_rate=tax_rate,
                        tax_amount=tax_amt,
                        amount=amount
                    )
                    product = Product.objects.get(pk=item['product_id'])
                    product.current_stock -= qty
                    product.save()
                    subtotal += amount
                    tax_total += tax_amt

            discount = Decimal(str(request.POST.get('discount', 0)))
            invoice.subtotal = subtotal
            invoice.tax_amount = tax_total
            invoice.discount = discount
            invoice.total_amount = subtotal + tax_total - discount
            invoice.save()
            messages.success(request, f'Invoice {invoice.invoice_number} updated!')
            return redirect(f'/sales/invoices/{invoice.pk}/')
        except Exception as e:
            import traceback
            messages.error(request, f'Error: {traceback.format_exc()}')

    # Pre-fill existing items for the form
    existing_items = []
    for item in invoice.items.select_related('product').all():
        existing_items.append({
            'product_id': str(item.product.pk),
            'name': item.product.name,
            'hsn': item.product.hsn_code or '',
            'unit': item.product.unit.name if item.product.unit else '',
            'qty': float(item.quantity),
            'rate': float(item.rate),
            'tax_rate': float(item.tax_rate),
            'tax_amt': float(item.tax_amount),
            'amount': float(item.amount),
        })

    import json
    context = {
        'invoice': invoice,
        'customers': customers,
        'products': products,
        'invoice_type': invoice_type,
        'invoice_number': invoice.invoice_number,
        'today': invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
        'due_date': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '',
        'existing_items_json': json.dumps(existing_items),
        'edit_mode': True,
    }
    return render(request, 'sales/invoice_form.html', context)

@login_required
def export_invoice(request):
    from masters.models import Customer, Product
    customers = Customer.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        try:
            import json
            from decimal import Decimal
            from django.utils import timezone

            inv_no = request.POST.get('invoice_number', '').strip()
            if not inv_no:
                from datetime import date
                yr = date.today().strftime('%y')
                count = SalesInvoice.objects.filter(invoice_type='export').count() + 1
                inv_no = f'EXP/{yr}/{str(count).zfill(3)}'

            invoice = SalesInvoice.objects.create(
                invoice_number=inv_no,
                invoice_type='export',
                customer_id=request.POST.get('customer'),
                invoice_date=request.POST.get('invoice_date'),
                due_date=request.POST.get('due_date') or None,
                currency=request.POST.get('currency', 'INR'),
                usd_rate=Decimal(str(request.POST.get('usd_rate', 0) or 0)),
                cad_rate=Decimal(str(request.POST.get('cad_rate', 0) or 0)),
                total_inr=Decimal(str(request.POST.get('total_inr', 0) or 0)),
                total_usd=Decimal(str(request.POST.get('total_usd', 0) or 0)),
                total_cad=Decimal(str(request.POST.get('total_cad', 0) or 0)),
                subtotal=Decimal(str(request.POST.get('subtotal', 0) or 0)),
                discount=Decimal(str(request.POST.get('discount', 0) or 0)),
                total_amount=Decimal(str(request.POST.get('total_amount', 0) or 0)),
                port_of_loading=request.POST.get('port_of_loading', ''),
                port_of_discharge=request.POST.get('port_of_discharge', ''),
                country_of_destination=request.POST.get('country_of_destination', ''),
                shipping_bill_no=request.POST.get('shipping_bill_no', ''),
                lut_number=request.POST.get('lut_number', ''),
                notes=request.POST.get('notes', ''),
                status=request.POST.get('status', 'pending'),
            )

            items_json = request.POST.get('items_json', '[]')
            items = json.loads(items_json)
            for item in items:
                if item.get('product'):
                    qty = Decimal(str(item.get('quantity', 1)))
                    rate = Decimal(str(item.get('rate', 0)))
                    rate_usd = Decimal(str(item.get('rate_usd', 0)))
                    rate_cad = Decimal(str(item.get('rate_cad', 0)))
                    amount = qty * rate
                    amount_usd = qty * rate_usd
                    amount_cad = qty * rate_cad
                    SalesInvoiceItem.objects.create(
                        invoice=invoice,
                        product_id=item['product'],
                        quantity=qty,
                        rate=rate,
                        rate_usd=rate_usd,
                        rate_cad=rate_cad,
                        tax_rate=Decimal('0'),
                        tax_amount=Decimal('0'),
                        amount=amount,
                        amount_usd=amount_usd,
                        amount_cad=amount_cad,
                    )
                    try:
                        p = Product.objects.get(pk=item['product'])
                        p.current_stock -= qty
                        p.save()
                    except: pass

            messages.success(request, f'Export Invoice {inv_no} saved!')
            return redirect(f'/sales/invoices/{invoice.pk}/')

        except Exception as e:
            import traceback
            messages.error(request, f'Error: {traceback.format_exc()}')

    # GET - show form
    from datetime import date
    yr = date.today().strftime('%y')
    count = SalesInvoice.objects.filter(invoice_type='export').count() + 1
    next_no = f'EXP/{yr}/{str(count).zfill(3)}'

    return render(request, 'sales/export_invoice.html', {
        'customers': customers,
        'products': products,
        'next_invoice_no': next_no,
    })
