from decimal import Decimal
from django.conf import settings
from django.http import HttpResponse, JsonResponse
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
    from masters.middleware import get_user_role
    return render(request, "sales/invoice_list.html", {
        "invoices": invoices,
        "invoice_type": invoice_type,
        "current_type": invoice_type,
        "from_date": from_date,
        "to_date": to_date,
        "query": query,
        "user_role": get_user_role(request.user),
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
                    customer_mobile=request.POST.get("customer_mobile", "").strip(),
                    customer_email=request.POST.get("customer_email", "").strip(),
                    subtotal=0, tax_amount=0, total_amount=0,
                    created_by=request.user
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
    from masters.middleware import get_user_role
    return render(request, "sales/invoice_detail.html", {
        "invoice": invoice,
        "user_role": get_user_role(request.user),
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

def _generate_invoice_pdf(request, pk):
    """Core PDF generation — no login check, called by both invoice_pdf and invoice_public_pdf."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, KeepTogether
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    import os
    try:
        from num2words import num2words as n2w
        has_n2w = True
    except:
        has_n2w = False

    invoice = get_object_or_404(SalesInvoice, pk=pk)
    items   = invoice.items.select_related("product").all()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=Invoice_{invoice.invoice_number}.pdf"

    LM = RM = 1*mm
    doc = SimpleDocTemplate(
        response, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=1*mm, bottomMargin=0.5*mm
    )
    W   = A4[0] - LM - RM
    elements = []

    # ── Style helper ────────────────────────────────────────
    _cache = {}
    def ps(name, sz=8, bold=False, align=TA_LEFT, color=colors.black):
        key = (name, sz, bold, align, color)
        if key not in _cache:
            _cache[key] = ParagraphStyle(
                name, fontSize=sz,
                fontName="Helvetica-Bold" if bold else "Helvetica",
                alignment=align, textColor=color,
                leading=sz + 2, spaceAfter=0, spaceBefore=0,
                splitLongWords=0, wordWrap=None)
        return _cache[key]

    BK   = colors.black
    BLUE = colors.HexColor("#1a237e")
    LBLU = colors.HexColor("#dce4f5")
    GRY  = colors.HexColor("#555555")

    def ts(*cmds): return TableStyle(list(cmds))
    def box(w=0.5): return ("BOX",(0,0),(-1,-1),w,BK)
    def grid(w=0.3): return ("INNERGRID",(0,0),(-1,-1),w,colors.HexColor("#aaaaaa"))
    def pad(p=3): return ("PADDING",(0,0),(-1,-1),p)
    def vmid(): return ("VALIGN",(0,0),(-1,-1),"MIDDLE")



    # ── 1. TOP STRIP: UDYAM | TAX INVOICE | Original For Buyer ──
    top = Table([[
        Paragraph("<b>UDYAM REG. NO : UDYAM-CH-01-0003053</b>", ps("ud", 9, bold=True, color=BK)),
        Paragraph("<b>TAX  INVOICE</b>", ps("ti", 20, bold=True, align=TA_CENTER, color=BLUE)),
        Paragraph("<b>Original For Buyer</b>", ps("ofb", 9, bold=True, align=TA_RIGHT, color=BK)),
    ]], colWidths=[W*0.30, W*0.40, W*0.30])
    top.setStyle(ts(pad(2), vmid()))
    elements.append(top)

    # ── 2. COMPANY LOGO (full width) ──────────────────────
    logo_path = os.path.join(settings.BASE_DIR, "company_bill_top_logo.png")
    if os.path.exists(logo_path):
        from reportlab.platypus import Image as RLImage
        from PIL import Image as PILImage
        with PILImage.open(logo_path) as im:
            orig_w, orig_h = im.size
        logo_img = RLImage(logo_path, width=W, height=W * orig_h / orig_w)
        elements.append(logo_img)
    # ── 3. GSTIN / INVOICE INFO ───────────────────────────
    inv_date = invoice.invoice_date.strftime("%d-%m-%Y") if hasattr(invoice.invoice_date, "strftime") else str(invoice.invoice_date)
    rc_text  = "Yes" if invoice.reverse_charge == "Y" else "No"
    info = Table([
        [Paragraph(f"GSTIN Number : <b>04ALVPK9235D1ZW</b>",         ps("i1",9)),
         Paragraph(f"Transportation Mode : {invoice.transport or ''}",ps("i2",9))],
        [Paragraph(f"Tax is Payable on Reverse Charge(Yes/No) : {rc_text}", ps("i3",9)),
         Paragraph(f"Veh. No : {invoice.vehicle_number or ''}",       ps("i4",9))],
        [Paragraph(f"Invoice Serial Number : <b>{invoice.invoice_number}</b>", ps("i5",9,bold=True)),
         Paragraph("Date &amp; Time of Supply :  -  -",               ps("i6",9))],
        [Paragraph(f"Invoice Date &nbsp;&nbsp;&nbsp; : <b>{inv_date}</b>", ps("i7",9,bold=True)),
         Paragraph(f"Place OF Supply : {invoice.place_of_supply or ''}",   ps("i8",9))],
    ], colWidths=[W*0.50, W*0.50])
    info.setStyle(ts(box(0.5), grid(0.3), pad(3), vmid()))
    elements.append(info)

    # ── 4. PARTY: BILLED TO  |  SHIPPED TO ───────────────
    cust = invoice.customer
    half = W / 2
    state_code = (cust.gstin[:2] if cust.gstin and len(cust.gstin) >= 2 else "") + (" -" + cust.state if cust.state else "")
    party = Table([
        [Paragraph("<b>Details of Receiver (Billed to)</b>",   ps("pb1",9,bold=True)),
         Paragraph("<b>Details of Consignee (Shipped to)</b>", ps("pb2",9,bold=True))],
        [Paragraph(f"Name : <b>{cust.name}</b>",  ps("p1",9)), Paragraph("Name :",   ps("p2",9))],
        [Paragraph(f"Address : {cust.address or ''}", ps("p3",9)), Paragraph("Address :", ps("p4",9))],
        [Paragraph("",ps("p5b",9)), Paragraph("",ps("p6b",9))],
        [Paragraph(f"State : {cust.state or ''}",ps("p5",9)),  Paragraph("State :",  ps("p6",9))],
        [Paragraph(f"State Code : {state_code}",ps("p7",9)), Paragraph("State Code :", ps("p8",9))],
        [Paragraph(f"GSTIN Number :  {cust.gstin or ''}",ps("p9",9)), Paragraph("GSTIN Number :", ps("p10",9))],
    ], colWidths=[half, half])
    party.setStyle(ts(box(0.5), grid(0.3), pad(2), vmid(),
        ("BACKGROUND",(0,0),(-1,0), LBLU),
        ("LINEAFTER",(0,0),(0,-1),0.5,BK),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
    ))
    elements.append(party)

    # ── 5. ORDER / GR INFO ────────────────────────────────
    gr_d  = invoice.gr_date.strftime("%d-%m-%Y")    if invoice.gr_date    else "- -"
    ord_d = invoice.order_date.strftime("%d-%m-%Y") if invoice.order_date else "- -"
    order = Table([
        [Paragraph(f"ORDER NO. &nbsp;&nbsp;: {invoice.order_number or ''}",ps("o1",9)),
         Paragraph(f"G.R.NO. : {invoice.gr_number or ''}",                 ps("o2",9))],
        [Paragraph(f"ORDER DATE : {ord_d}", ps("o3",9)),
         Paragraph(f"G.R.DATE : {gr_d}",   ps("o4",9))],
    ], colWidths=[W*0.50, W*0.50])
    order.setStyle(ts(box(0.5), grid(0.3), pad(3), vmid()))
    elements.append(order)

    # ── 6. ITEMS TABLE ────────────────────────────────────
    # Cols: S.NO | Description | HSN/SAC | Qty | UOM | Rate | Taxable Rs. | CGST R | CGST A | UTGST R | UTGST A | IGST R | IGST A
    # 13 columns, NO DIS, NO last Amount col (matches sample image)
    # S.NO | Description | HSN | Qty | UOM | Rate | Taxable | CGST% | CGST Amt | UTGST% | UTGST Amt | IGST% | IGST Amt
    # Total must equal W (208mm) to prevent overflow
    cw = [7*mm, 40*mm, 16*mm, 9*mm, 11*mm, 22*mm, 22*mm,
          10*mm, 18*mm, 10*mm, 18*mm, 9*mm, 16*mm]
    # 7+40+16+9+11+22+22+10+18+10+18+9+16 = 208mm = W
    # verify total ≈ W
    # 7+42+16+9+9+15+18+9+15+9+15+9+17 = 190mm — pad description to fill W
    cw[1] = W - sum(cw) + cw[1]

    def H(t,n):  return Paragraph(f"<b>{t}</b>", ps(n,7,bold=True,align=TA_CENTER))
    def CR(t,n): return Paragraph(t, ps(n,9,align=TA_RIGHT))
    def CC(t,n): return Paragraph(t, ps(n,9,align=TA_CENTER))

    hdr0 = [H("S.\nNO","h0"), H("Description of Goods","h1"), H("HSN Code\n/ SAC","h2"),
            H("Qty","h3"), H("UOM","h4"), H("Rate","h5"),
            H("Taxable\nValue\nRs.","h6"),
            H("CGST","hcg"),   Paragraph("",ps("hcg2",7)),
            H("UTGST","hug"),  Paragraph("",ps("hug2",7)),
            H("IGST","hig"),   Paragraph("",ps("hig2",7))]
    hdr1 = [Paragraph("",ps(f"hx{i}",7)) for i in range(7)] + [
            H("Rate\n%","hcgr"), H("Amount","hcga"),
            H("Rate\n%","hugr"), H("Amount","huga"),
            H("Rate\n%","higr"), H("Amount","higa")]
    rows = [hdr0, hdr1]

    is_inter     = (invoice.gst_type == 'I')
    total_taxable= 0.0
    total_cgst   = 0.0
    total_igst   = 0.0

    for idx, item in enumerate(items, 1):
        dis_pct   = float(item.discount_pct or 0)
        taxable   = float(item.quantity) * float(item.rate) * (1 - dis_pct/100)
        full_rate = float(item.tax_rate)
        half_rate = full_rate / 2
        if is_inter:
            igst_amt = taxable * full_rate / 100
            cgst_amt = 0.0
        else:
            cgst_amt = taxable * half_rate / 100
            igst_amt = 0.0
        total_taxable += taxable
        total_cgst    += cgst_amt
        total_igst    += igst_amt
        uname  = item.unit or (str(item.product.unit) if item.product and item.product.unit else "NOS")
        hsn    = item.hsn_no or (item.product.hsn_code if item.product else "") or ""
        iname  = item.description or (item.product.name if item.product else "")
        # Truncate very long descriptions to 2 display lines (~90 chars for this column width)
        rows.append([
            CC(str(idx),              f"rno{idx}"),
            Paragraph(iname,          ParagraphStyle(f"rd{idx}", fontSize=9,
                          fontName="Helvetica", alignment=TA_LEFT,
                          leading=11, spaceAfter=0, spaceBefore=0,
                          splitLongWords=0, wordWrap='LTR')),
            CC(hsn,                   f"rh{idx}"),
            CC(str(int(item.quantity)) if float(item.quantity) == int(float(item.quantity)) else str(item.quantity), f"rq{idx}"),
            CC(uname,                 f"ru{idx}"),
            CR(f"{float(item.rate):.2f}", f"rr{idx}"),
            CR(f"{taxable:.2f}",      f"rt{idx}"),
            CC(f"{half_rate:.2f}" if not is_inter else "0.00", f"rcgr{idx}"),
            CR(f"{cgst_amt:.2f}",     f"rcga{idx}"),
            CC(f"{half_rate:.2f}" if not is_inter else "0.00", f"rugr{idx}"),
            CR(f"{cgst_amt:.2f}" if not is_inter else "0.00",  f"ruga{idx}"),
            CC(f"{full_rate:.2f}" if is_inter else "0.00",     f"rigr{idx}"),
            CR(f"{igst_amt:.2f}",     f"riga{idx}"),
        ])

    # Bottom sections are built below; items table is built after measuring everything.

    # ── 7. INVOICE VALUE IN WORDS + GST TOTALS ROW ───────
    curr       = invoice.currency or 'INR'
    sym        = {'INR':'Rs.','USD':'USD $','CAD':'CAD $'}.get(curr,'Rs.')
    usd_rate   = float(invoice.usd_rate or 0)
    cad_rate   = float(invoice.cad_rate or 0)
    total_inr  = float(invoice.total_amount or 0)
    total_usd  = float(invoice.total_usd or 0) or (total_inr/usd_rate if usd_rate else 0)
    total_cad  = float(invoice.total_cad or 0) or (total_inr/cad_rate if cad_rate else 0)
    try:
        words = sym + (n2w(int(invoice.total_amount), lang="en_IN").title() if has_n2w else f"{invoice.total_amount:.2f}") + " only"
    except:
        words = f"{sym}{invoice.total_amount:.2f} only"

    # Words row — left spans all cols except the 3 GST Amount cols
    _wleft = W - cw[8] - cw[10] - cw[12]
    wrow = Table([[
        Paragraph(f"Invoice Value (In Words) &nbsp; <b>{words}</b>", ps("ww",9)),
        Paragraph(f"Rs. {total_cgst:.2f}",                                   ps("wcg",9,align=TA_RIGHT)),
        Paragraph(f"Rs. {total_cgst:.2f}" if not is_inter else "Rs. 0.00",  ps("wug",9,align=TA_RIGHT)),
        Paragraph(f"Rs. {total_igst:.2f}",                                   ps("wig",9,align=TA_RIGHT)),
    ]], colWidths=[_wleft, cw[8], cw[10], cw[12]])
    wrow.setStyle(ts(box(0.6), pad(4), vmid()))

    # ── 8. REMARKS / BANK  |  TOTALS  ─────────────────────
    tax_total = total_cgst * 2 if not is_inter else total_igst
    due_str   = invoice.due_date.strftime("%d-%m-%Y") if invoice.due_date else ""

    bank_tbl = Table([
        [Paragraph("<b>BANK NAME</b>", ps("bk1",9,bold=True)), Paragraph(":", ps("bkc",9)), Paragraph("<b>ICICI BANK</b>", ps("bk1v",9,bold=True))],
        [Paragraph("A/c No",           ps("bk2",9)),           Paragraph(":", ps("bkc2",9)), Paragraph("632205005712",      ps("bk2v",9))],
        [Paragraph("BRANCH",           ps("bk3",9)),           Paragraph(":", ps("bkc3",9)), Paragraph("SECTOR 35C",        ps("bk3v",9))],
        [Paragraph("IFSC CODE",        ps("bk4",9)),           Paragraph(":", ps("bkc4",9)), Paragraph("ICIC0006322",       ps("bk4v",9))],
    ], colWidths=[22*mm, 4*mm, None])
    bank_tbl.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),1),("BOTTOMPADDING",(0,0),(-1,-1),1),
                                   ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),2),
                                   ("VALIGN",(0,0),(-1,-1),"MIDDLE")]))

    left_cell = [
        Paragraph("<b>REMARKS:</b>", ps("rem",9,bold=True)),
        Paragraph(invoice.notes or "", ps("remn",9)),
        Spacer(1,3*mm),
        Paragraph(f"DUE DATE : {due_str}", ps("dd",9)),
        Spacer(1,3*mm),
        bank_tbl,
    ]

    right_rows = [
        [Paragraph("Total Amount Before Tax", ps("ta1",9)),
         Paragraph(f"Rs.", ps("ta1s",9,align=TA_RIGHT)),
         Paragraph(f"{total_taxable:.2f}", ps("ta1a",9,align=TA_RIGHT))],
        [Paragraph("ADD: CGST", ps("ta2",9)),
         Paragraph("Rs.", ps("ta2s",9,align=TA_RIGHT)),
         Paragraph(f"{total_cgst:.2f}", ps("ta2a",9,align=TA_RIGHT))],
        [Paragraph("ADD: UTGST", ps("ta3",9)),
         Paragraph("Rs.", ps("ta3s",9,align=TA_RIGHT)),
         Paragraph(f"{total_cgst:.2f}" if not is_inter else "0.00", ps("ta3a",9,align=TA_RIGHT))],
        [Paragraph("ADD: IGST", ps("ta4",9)),
         Paragraph("Rs.", ps("ta4s",9,align=TA_RIGHT)),
         Paragraph(f"{total_igst:.2f}", ps("ta4a",9,align=TA_RIGHT))],
        [Paragraph("Tax Amount : GST", ps("ta5",9)),
         Paragraph("Rs.", ps("ta5s",9,align=TA_RIGHT)),
         Paragraph(f"{tax_total:.2f}", ps("ta5a",9,align=TA_RIGHT))],
        [Paragraph("", ps("ta6",9)), Paragraph("Rs.", ps("ta6s",9,align=TA_RIGHT)),
         Paragraph("", ps("ta6a",9))],
    ]
    if curr == 'USD' and usd_rate:
        right_rows.append([Paragraph(f"Exch Rate 1 USD=Rs.{usd_rate:.2f}",ps("ta7",9)),
                           Paragraph("USD$",ps("ta7s",9,align=TA_RIGHT)),
                           Paragraph(f"{total_usd:.2f}",ps("ta7a",9,align=TA_RIGHT))])
    if curr == 'CAD' and cad_rate:
        right_rows.append([Paragraph(f"Exch Rate 1 CAD=Rs.{cad_rate:.2f}",ps("ta8",9)),
                           Paragraph("CAD$",ps("ta8s",9,align=TA_RIGHT)),
                           Paragraph(f"{total_cad:.2f}",ps("ta8a",9,align=TA_RIGHT))])
    right_rows.append([
        Paragraph("<b>Total Amount After Tax :</b>", ps("taf",9,bold=True)),
        Paragraph("<b>Rs.</b>", ps("tafs",9,bold=True,align=TA_RIGHT)),
        Paragraph(f"<b>{total_inr:.2f}</b>", ps("tafa",9,bold=True,align=TA_RIGHT)),
    ])

    right_tbl = Table(right_rows, colWidths=[55*mm, 8*mm, 25*mm])
    NRR = len(right_rows)
    right_tbl.setStyle(TableStyle([
        box(0.5), pad(3), vmid(),
        ("INNERGRID",(0,0),(-1,-1),0.2,colors.HexColor("#cccccc")),
        ("BACKGROUND",(0,NRR-1),(-1,NRR-1),LBLU),
        ("FONTNAME",(0,NRR-1),(-1,NRR-1),"Helvetica-Bold"),
        ("ALIGN",(1,0),(-1,-1),"RIGHT"),
    ]))

    RW = 88*mm   # right column width
    LW = W - RW
    from reportlab.platypus import ListFlowable
    bottom = Table([[
        left_cell,
        right_tbl,
    ]], colWidths=[LW, RW])
    bottom.setStyle(ts(box(0.5), pad(4), vmid(),
        ("LINEAFTER",(0,0),(0,0),0.5,BK),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ))
    # ── 9. CERTIFIED + FOR CTC ────────────────────────────
    stamp_path = os.path.join(settings.BASE_DIR, "signature_stamp.png")
    if os.path.exists(stamp_path):
        from reportlab.platypus import Image as RLImage
        from PIL import Image as PILImage
        with PILImage.open(stamp_path) as _im:
            _sw, _sh = _im.size
        _stamp_h = 28*mm
        _stamp_w = min(_stamp_h * _sw / _sh, RW - 4)
        stamp_cell = RLImage(stamp_path, width=_stamp_w, height=_stamp_h)
    else:
        stamp_cell = Paragraph("", ps("sigSp",9))

    sig_inner = Table([
        [Paragraph("<b>For CHANDIGARH TEAM COMPUTERS</b>", ps("sigH",9,bold=True,align=TA_CENTER))],
        [stamp_cell],
        [Paragraph("<b>Authorised Signatory</b>", ps("sigF",9,bold=True,align=TA_CENTER))],
    ], colWidths=[RW - 2], rowHeights=[8*mm, 30*mm, 7*mm])
    sig_inner.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LINEABOVE",     (0,2),(-1,2),  0.6, BK),
    ]))
    cert_sig = Table([[
        Paragraph("Certified that the Particulars given above are true and correct",
                  ps("cert",9,color=GRY)),
        sig_inner,
    ]], colWidths=[LW, RW])
    cert_sig.setStyle(ts(box(0.5), pad(5), vmid(),
        ("LINEAFTER", (0,0),(0,0), 0.5, BK),
        ("VALIGN",    (0,0),(0,0), "MIDDLE"),
        ("VALIGN",    (1,0),(1,0), "MIDDLE"),
        ("TOPPADDING",(1,0),(1,0), 3),
        ("BOTTOMPADDING",(1,0),(1,0), 3),
        ("LEFTPADDING",(1,0),(1,0), 1),
        ("RIGHTPADDING",(1,0),(1,0), 1),
    ))

    # ── 10. TERMS & CONDITIONS ────────────────────────────
    tc = Table([[
        Paragraph(
            "<b>TERM &amp; CONDITION</b><br/>"
            "1. Our responsibility ceases as soon as the goods are handed over to Carrier/customer.<br/>"
            "2. All Disputes subject to Chandigarh Juridiction.<br/>"
            "3. Interest @ Rs.24% p.a. will be charged on all amounts remained unpaid after 15 days..",
            ps("tc",9)),
    ]], colWidths=[W])
    tc.setStyle(ts(box(0.5), pad(5)))

    # ── Build items table with filler rows inside it (guarantees column alignment) ──
    from reportlab.platypus import KeepTogether

    # Measure bottom sections
    _, h1 = wrow.wrap(W, 9999*mm)
    _, h2 = bottom.wrap(W, 9999*mm)
    _, h3 = cert_sig.wrap(W, 9999*mm)
    _, h4 = tc.wrap(W, 9999*mm)
    reserve = h1 + h2 + h3 + h4 + 1*mm

    # Measure top elements already in elements[]
    top_total = 0
    for el in elements:
        _, eh = el.wrap(W, 9999*mm)
        top_total += eh

    # Measure current items rows height (temp table, no filler)
    _tmp = Table(rows, colWidths=cw)
    _, items_h = _tmp.wrap(W, 9999*mm)

    # Calculate how many 6mm filler rows fit in remaining space
    PAGE_H = A4[1] - doc.topMargin - doc.bottomMargin
    FILLER_H = 6 * mm
    remaining = PAGE_H - top_total - items_h - reserve
    n_filler = max(0, int(remaining / FILLER_H))
    NR_data = len(rows)

    # Add filler rows directly into items table
    BK_ALT = colors.HexColor("#f4f6fc")
    for _ in range(n_filler):
        rows.append([""] * 13)

    NR = len(rows)
    row_heights = [None, None] + [None] * (NR_data - 2) + [FILLER_H] * n_filler
    itbl = Table(rows, colWidths=cw, rowHeights=row_heights, repeatRows=2)
    itbl.setStyle(TableStyle([
        box(0.6), grid(0.25), pad(3), vmid(),
        ("BACKGROUND", (0, 0), (-1, 1), LBLU),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 2), (-1, NR - 1), [colors.white, BK_ALT]),
        ("SPAN", (0, 0), (0, 1)), ("SPAN", (1, 0), (1, 1)), ("SPAN", (2, 0), (2, 1)),
        ("SPAN", (3, 0), (3, 1)), ("SPAN", (4, 0), (4, 1)), ("SPAN", (5, 0), (5, 1)),
        ("SPAN", (6, 0), (6, 1)),
        ("SPAN", (7, 0), (8, 0)), ("SPAN", (9, 0), (10, 0)), ("SPAN", (11, 0), (12, 0)),
        ("LINEBEFORE", (7, 0), (-1, -1), 0.6, BK),
        ("LINEBEFORE", (9, 0), (-1, -1), 0.6, BK),
        ("LINEBEFORE", (11, 0), (-1, -1), 0.6, BK),
    ]))
    elements.append(itbl)
    elements.append(KeepTogether([wrow, bottom, cert_sig, tc]))

    doc.build(elements)
    return response


@login_required
def invoice_pdf(request, pk):
    """Login-protected wrapper — used from browser by logged-in staff."""
    return _generate_invoice_pdf(request, pk)


# ── Public PDF: no login required, accessed via share token ──────────────
def invoice_public_pdf(request, token):
    """Public PDF via unique share token — no login needed for customers."""
    invoice = get_object_or_404(SalesInvoice, share_token=token)
    return _generate_invoice_pdf(request, invoice.pk)


# ── WhatsApp: open wa.me link with pre-filled invoice message ─────────────
@login_required
def invoice_whatsapp(request, pk):
    """Returns a wa.me URL so the browser can open WhatsApp with a pre-filled message."""
    import secrets
    from urllib.parse import quote
    invoice = get_object_or_404(SalesInvoice, pk=pk)
    cust    = invoice.customer

    # Generate share token if not already set
    if not invoice.share_token:
        invoice.share_token = secrets.token_urlsafe(32)
        invoice.save(update_fields=['share_token'])

    # Build public PDF link
    from django.conf import settings as django_settings
    base_url = django_settings.SITE_URL.rstrip('/')
    pdf_link = f"{base_url}/sales/invoices/public/{invoice.share_token}/pdf/"

    # Pick best phone: invoice-level override → customer mobile → customer phone
    phone = (invoice.customer_mobile or cust.mobile or cust.phone or "").strip()
    phone = "".join(c for c in phone if c.isdigit())
    if phone and not phone.startswith("91") and len(phone) == 10:
        phone = "91" + phone

    due = invoice.due_date.strftime("%d-%m-%Y") if invoice.due_date else "—"
    msg = (
        f"Dear {cust.name},\n\n"
        f"Please find your invoice details below:\n"
        f"Invoice No : {invoice.invoice_number}\n"
        f"Date       : {invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else ''}\n"
        f"Amount     : Rs. {invoice.total_amount}\n"
        f"Due Date   : {due}\n"
        f"Balance    : Rs. {invoice.balance_due}\n\n"
        f"View / Download Invoice PDF:\n{pdf_link}\n\n"
        f"For any queries, contact us at: 7986810335\n"
        f"— Chandigarh Team Computers"
    )

    if phone:
        wa_url = f"https://wa.me/{phone}?text={quote(msg)}"
    else:
        wa_url = f"https://wa.me/?text={quote(msg)}"

    return JsonResponse({"url": wa_url, "phone": phone})


# ── Email: send PDF invoice as attachment via Gmail SMTP ──────────────────
@login_required
def invoice_send_email(request, pk):
    """Sends the invoice PDF as an email attachment to the customer (or a custom address)."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    import io
    from django.core.mail import EmailMessage
    from django.conf import settings as django_settings

    invoice  = get_object_or_404(SalesInvoice, pk=pk)
    cust     = invoice.customer
    to_email = request.POST.get("email", "").strip() or invoice.customer_email or cust.email

    if not to_email:
        return JsonResponse({"error": "No email address provided."}, status=400)

    if not django_settings.EMAIL_HOST_USER:
        return JsonResponse({"error": "Email is not configured. Please set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in environment variables."}, status=500)

    # Generate share token for public PDF link
    import secrets
    if not invoice.share_token:
        invoice.share_token = secrets.token_urlsafe(32)
        invoice.save(update_fields=['share_token'])
    base_url = django_settings.SITE_URL.rstrip('/')
    pdf_link = f"{base_url}/sales/invoices/public/{invoice.share_token}/pdf/"

    # Generate PDF in memory
    pdf_response = _generate_invoice_pdf(request, pk)
    pdf_bytes    = pdf_response.content

    subject = f"Invoice {invoice.invoice_number} from Chandigarh Team Computers"
    body    = (
        f"Dear {cust.name},\n\n"
        f"Please find your invoice attached to this email.\n"
        f"You can also view/download it here: {pdf_link}\n\n"
        f"Invoice No : {invoice.invoice_number}\n"
        f"Date       : {invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else ''}\n"
        f"Amount     : Rs. {invoice.total_amount}\n"
        f"Balance Due: Rs. {invoice.balance_due}\n\n"
        f"Thank you for your business!\n\n"
        f"Regards,\nChandigarh Team Computers\nPhone: 7986810335"
    )

    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=f"Chandigarh Team Computers <{django_settings.EMAIL_HOST_USER}>",
            to=[to_email],
        )
        email.attach(
            f"Invoice_{invoice.invoice_number}.pdf",
            pdf_bytes,
            "application/pdf",
        )
        email.send(fail_silently=False)
        return JsonResponse({"success": True, "message": f"Invoice sent to {to_email}"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




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
            with transaction.atomic():
                def _date(key):
                    v = request.POST.get(key, '').strip()
                    return v if v else None

                # Restore stock for old items then delete them
                for old_item in invoice.items.select_related('product').all():
                    if old_item.product:
                        old_item.product.current_stock += Decimal(str(old_item.quantity))
                        old_item.product.save()
                invoice.items.all().delete()

                # Update invoice header fields
                invoice.customer_id    = request.POST.get('customer')
                invoice.invoice_date   = request.POST.get('invoice_date')
                invoice.due_date       = _date('due_date')
                invoice.notes          = request.POST.get('notes', '')
                invoice.reverse_charge = request.POST.get('reverse_charge', 'N')
                invoice.gst_type       = request.POST.get('gst_type', 'W')
                invoice.gr_number      = request.POST.get('gr_number', '')
                invoice.gr_date        = _date('gr_date')
                invoice.date_of_supply = _date('date_of_supply')
                invoice.time_of_supply = request.POST.get('time_of_supply', '') or None
                invoice.place_of_supply= request.POST.get('place_of_supply', '')
                invoice.order_number   = request.POST.get('order_number', '')
                invoice.order_date     = _date('order_date')
                invoice.vehicle_number = request.POST.get('vehicle_number', '')
                invoice.transport      = request.POST.get('transport', '')
                invoice.despatched_to  = request.POST.get('despatched_to', '')
                invoice.add_less1_label= request.POST.get('add_less1_label', '')
                invoice.add_less1      = Decimal(str(request.POST.get('add_less1', 0) or 0))
                invoice.add_less2_label= request.POST.get('add_less2_label', '')
                invoice.add_less2      = Decimal(str(request.POST.get('add_less2', 0) or 0))
                invoice.bill_discount_pct = Decimal(str(request.POST.get('bill_discount_pct', 0) or 0))
                invoice.customer_mobile = request.POST.get('customer_mobile', '').strip()
                invoice.customer_email  = request.POST.get('customer_email', '').strip()

                # Re-add items (same logic as invoice_add)
                product_ids   = request.POST.getlist('product[]')
                descriptions  = request.POST.getlist('description[]')
                quantities    = request.POST.getlist('quantity[]')
                rates         = request.POST.getlist('rate[]')
                tax_rates     = request.POST.getlist('tax_rate[]')
                hsn_nos       = request.POST.getlist('hsn_no[]')
                units         = request.POST.getlist('unit[]')
                discount_pcts = request.POST.getlist('discount_pct[]')
                subtotal = 0; tax_total = 0
                for i in range(len(quantities)):
                    pid  = product_ids[i] if i < len(product_ids) else ''
                    desc = descriptions[i].strip() if i < len(descriptions) else ''
                    if not pid and not desc:
                        continue
                    qty     = float(quantities[i] or 0)
                    rate    = float(rates[i] or 0)
                    tax     = float(tax_rates[i] or 0)
                    dis_pct = float(discount_pcts[i] if i < len(discount_pcts) else 0 or 0)
                    dis_amt = rate * qty * dis_pct / 100
                    amount  = qty * rate - dis_amt
                    tax_amt = amount * tax / 100
                    SalesInvoiceItem.objects.create(
                        invoice=invoice,
                        product_id=pid if pid else None,
                        description=desc,
                        hsn_no=hsn_nos[i] if i < len(hsn_nos) else '',
                        unit=units[i] if i < len(units) else '',
                        quantity=qty, rate=rate,
                        discount_pct=Decimal(str(dis_pct)),
                        discount_amt=Decimal(str(round(dis_amt, 2))),
                        tax_rate=tax, tax_amount=tax_amt, amount=amount
                    )
                    if pid:
                        product = Product.objects.get(pk=pid)
                        product.current_stock -= Decimal(str(qty))
                        product.save()
                    subtotal += amount; tax_total += tax_amt

                discount = float(request.POST.get('discount', 0) or 0)
                bill_discount_pct = float(request.POST.get('bill_discount_pct', 0) or 0)
                bill_discount_amt = (subtotal + tax_total) * bill_discount_pct / 100
                al1 = float(request.POST.get('add_less1', 0) or 0)
                al2 = float(request.POST.get('add_less2', 0) or 0)
                net = subtotal + tax_total + al1 + al2 - discount - bill_discount_amt
                invoice.subtotal      = subtotal
                invoice.tax_amount    = tax_total
                invoice.discount      = discount
                invoice.total_amount  = net
                invoice.net_rounded   = round(net)
                invoice.save()
                messages.success(request, f'Invoice {invoice.invoice_number} updated!')
                return redirect(f'/sales/invoices/{invoice.pk}/')
        except Exception as e:
            messages.error(request, f'Error: {traceback.format_exc()}')

    # Pre-fill existing items for the form
    existing_items = []
    for item in invoice.items.select_related('product').all():
        if item.product:
            existing_items.append({
                'product_id': str(item.product.pk),
                'name': item.description or item.product.name,
                'hsn': item.hsn_no or item.product.hsn_code or '',
                'unit': item.unit or (str(item.product.unit) if item.product.unit else ''),
                'qty': float(item.quantity),
                'rate': float(item.rate),
                'tax_rate': float(item.tax_rate),
                'dis_pct': float(item.discount_pct or 0),
                'amount': float(item.amount),
                'description': item.description or '',
            })
        else:
            existing_items.append({
                'product_id': '',
                'name': '',
                'hsn': item.hsn_no or '',
                'unit': item.unit or '',
                'qty': float(item.quantity),
                'rate': float(item.rate),
                'tax_rate': float(item.tax_rate),
                'dis_pct': float(item.discount_pct or 0),
                'amount': float(item.amount),
                'description': item.description or '',
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
