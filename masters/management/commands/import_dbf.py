"""
Management command to import data from CTC VFP DBF files into Django.

Usage:
    python manage.py import_dbf                    # import everything
    python manage.py import_dbf --path D:/CTC24    # custom path
    python manage.py import_dbf --only customers
    python manage.py import_dbf --only vendors
    python manage.py import_dbf --only products
    python manage.py import_dbf --only invoices
    python manage.py import_dbf --only purchases
    python manage.py import_dbf --only states
    python manage.py import_dbf --clear            # wipe before import
"""

import os
import datetime
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

DEFAULT_PATH = r"D:\CTC24"
ENCODING = "cp1252"


def open_dbf(path, filename):
    import dbfread
    full = os.path.join(path, filename)
    if not os.path.exists(full):
        return []
    try:
        return list(dbfread.DBF(full, encoding=ENCODING, ignore_missing_memofile=True))
    except Exception as e:
        print(f"  [WARN] Cannot read {filename}: {e}")
        return []


def s(val, default=""):
    if val is None:
        return default
    return str(val).strip()


def d(val):
    if val is None:
        return None
    if isinstance(val, datetime.date):
        return val
    return None


def dec(val, default=0):
    if val is None:
        return Decimal(str(default))
    try:
        return Decimal(str(float(val))).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(str(default))


class Command(BaseCommand):
    help = "Import all data from CTC VFP DBF files"

    def add_arguments(self, parser):
        parser.add_argument("--path", default=DEFAULT_PATH, help="Path to DBF folder")
        parser.add_argument(
            "--only",
            choices=["customers", "products", "vendors", "invoices", "purchases", "states"],
            help="Import only one module",
        )
        parser.add_argument("--clear", action="store_true", help="Delete existing data before import")

    def handle(self, *args, **options):
        self.path = options["path"]
        only = options.get("only")
        clear = options.get("clear", False)

        if not os.path.isdir(self.path):
            raise CommandError(f"DBF folder not found: {self.path}")

        self.stdout.write(self.style.SUCCESS(f"\n{'='*55}"))
        self.stdout.write(self.style.SUCCESS(f"  CTC DBF Import  —  {self.path}"))
        self.stdout.write(self.style.SUCCESS(f"{'='*55}\n"))

        # Clear order matters: dependents first
        if clear and not only:
            self.stdout.write("Clearing existing data (dependents first)...")
            from sales.models import SalesInvoice, SalesInvoiceItem
            from purchase.models import PurchaseBill, PurchaseBillItem
            from masters.models import Customer, Vendor, Product, Unit, GSTStateCode
            SalesInvoiceItem.objects.all().delete()
            SalesInvoice.objects.all().delete()
            try:
                PurchaseBillItem.objects.all().delete()
            except Exception:
                pass
            PurchaseBill.objects.all().delete()
            Product.objects.all().delete()
            Customer.objects.all().delete()
            Vendor.objects.all().delete()
            Unit.objects.all().delete()
            GSTStateCode.objects.all().delete()
            self.stdout.write(self.style.WARNING("  All existing data cleared.\n"))
            clear = False  # individual methods should NOT clear again

        if only == "states" or not only:
            self.import_states(clear)
        if only == "customers" or not only:
            self.import_customers(clear)
        if only == "vendors" or not only:
            self.import_vendors(clear)
        if only == "products" or not only:
            self.import_products(clear)
        if only == "invoices" or not only:
            self.import_invoices(clear)
        if only == "purchases" or not only:
            self.import_purchases(clear)

        self.stdout.write(self.style.SUCCESS(f"\n{'='*55}"))
        self.stdout.write(self.style.SUCCESS("  Import Complete!"))
        self.stdout.write(self.style.SUCCESS(f"{'='*55}\n"))

    # ── helpers ──────────────────────────────────────────────

    def _cust_map(self):
        """
        CUST_MST: CODE = salesman code (S001 for all), CCODE = actual party code (C008, M002…)
        Returns dict: CCODE -> Customer ORM object
        """
        from masters.models import Customer
        rows = open_dbf(self.path, "CUST_MST.DBF")
        m = {}
        for r in rows:
            ccode = s(r.get("CCODE"))
            name  = s(r.get("CNAME"))
            if not ccode or not name:
                continue
            try:
                m[ccode] = Customer.objects.get(name=name)
            except Customer.DoesNotExist:
                pass
        return m

    def _vendor_map(self):
        """Same table, VEND_CODE marks who is a vendor — but all can be vendors."""
        from masters.models import Vendor
        rows = open_dbf(self.path, "CUST_MST.DBF")
        m = {}
        for r in rows:
            ccode = s(r.get("CCODE"))
            name  = s(r.get("CNAME"))
            if not ccode or not name:
                continue
            try:
                m[ccode] = Vendor.objects.get(name=name)
            except Vendor.DoesNotExist:
                pass
        return m

    def _prod_map(self):
        """item.DBF: I_CODE -> Product ORM object"""
        from masters.models import Product
        rows = open_dbf(self.path, "item.DBF")
        m = {}
        for r in rows:
            code = s(r.get("I_CODE"))
            name = s(r.get("I_NAME"))
            if not code:
                continue
            try:
                m[code] = Product.objects.get(name=name)
            except Product.DoesNotExist:
                pass
        return m

    # ── STATES ───────────────────────────────────────────────
    def import_states(self, clear=False):
        from masters.models import GSTStateCode
        rows = open_dbf(self.path, "GSTATE.DBF")
        self.stdout.write(f"[States]  {len(rows)} records in GSTATE.DBF")
        if clear:
            GSTStateCode.objects.all().delete()
        created = skipped = 0
        with transaction.atomic():
            for r in rows:
                code = s(r.get("GNAME"))    # e.g. "04"
                name = s(r.get("STNAME"))   # e.g. "CHANDIGARH"
                if not code or not name:
                    skipped += 1
                    continue
                _, new = GSTStateCode.objects.get_or_create(
                    state_code=code, defaults={"state_name": name.title()}
                )
                if new:
                    created += 1
                else:
                    skipped += 1
        self.stdout.write(self.style.SUCCESS(f"  OK {created} created, {skipped} already existed\n"))

    # ── CUSTOMERS ────────────────────────────────────────────
    def import_customers(self, clear=False):
        from masters.models import Customer
        rows = open_dbf(self.path, "CUST_MST.DBF")
        self.stdout.write(f"[Customers]  {len(rows)} records in CUST_MST.DBF")
        if clear:
            Customer.objects.all().delete()
        created = skipped = 0
        with transaction.atomic():
            for r in rows:
                name = s(r.get("CNAME"))
                if not name:
                    skipped += 1
                    continue
                addr_parts = [s(r.get("CADD1")), s(r.get("CADD2")), s(r.get("CADD3"))]
                address = ", ".join(p for p in addr_parts if p)
                city = s(r.get("CADD2")) or s(r.get("CADD3"))
                defaults = {
                    "phone":           s(r.get("CPHNO")),
                    "email":           s(r.get("E_MAIL")),
                    "gstin":           s(r.get("GST_NO")),
                    "address":         address,
                    "city":            city,
                    "state":           s(r.get("STNAME")),
                    "opening_balance": dec(r.get("CYOB")),
                    "is_active":       s(r.get("CSTAT")) != "D",
                }
                _, new = Customer.objects.get_or_create(name=name, defaults=defaults)
                if new:
                    created += 1
                else:
                    skipped += 1
        self.stdout.write(self.style.SUCCESS(f"  OK {created} created, {skipped} already existed\n"))

    # ── VENDORS ──────────────────────────────────────────────
    def import_vendors(self, clear=False):
        from masters.models import Vendor
        rows = open_dbf(self.path, "CUST_MST.DBF")
        # vendors = rows that have a VEND_CODE set; if none, import all
        vendor_rows = [r for r in rows if s(r.get("VEND_CODE"))]
        if not vendor_rows:
            vendor_rows = rows   # fallback: all parties can be vendors
        self.stdout.write(f"[Vendors]  {len(vendor_rows)} records (from CUST_MST VEND_CODE)")
        if clear:
            Vendor.objects.all().delete()
        created = skipped = 0
        with transaction.atomic():
            for r in vendor_rows:
                name = s(r.get("CNAME"))
                if not name:
                    skipped += 1
                    continue
                addr_parts = [s(r.get("CADD1")), s(r.get("CADD2")), s(r.get("CADD3"))]
                address = ", ".join(p for p in addr_parts if p)
                defaults = {
                    "phone":           s(r.get("CPHNO")),
                    "email":           s(r.get("E_MAIL")),
                    "gstin":           s(r.get("GST_NO")),
                    "address":         address,
                    "city":            s(r.get("CADD2")) or s(r.get("CADD3")),
                    "state":           s(r.get("STNAME")),
                    "opening_balance": dec(r.get("CYOB")),
                    "is_active":       s(r.get("CSTAT")) != "D",
                }
                _, new = Vendor.objects.get_or_create(name=name, defaults=defaults)
                if new:
                    created += 1
                else:
                    skipped += 1
        self.stdout.write(self.style.SUCCESS(f"  OK {created} created, {skipped} already existed\n"))

    # ── PRODUCTS ─────────────────────────────────────────────
    def import_products(self, clear=False):
        from masters.models import Product, Unit
        rows = open_dbf(self.path, "item.DBF")
        self.stdout.write(f"[Products]  {len(rows)} records in item.DBF")
        if clear:
            Product.objects.all().delete()
        created = skipped = 0
        with transaction.atomic():
            for r in rows:
                name = s(r.get("I_NAME"))
                code = s(r.get("I_CODE"))
                if not name:
                    skipped += 1
                    continue
                unit_name = s(r.get("UNIT")) or "NOS"
                unit_obj, _ = Unit.objects.get_or_create(
                    name=unit_name, defaults={"short_name": unit_name[:10]}
                )
                defaults = {
                    "code":           code or name[:20],
                    "unit":           unit_obj,
                    "hsn_code":       s(r.get("HS_CODE")),
                    "purchase_price": dec(r.get("PRATE")),
                    "sale_price":     dec(r.get("RATE")),
                    "tax_rate":       dec(r.get("GS_RT")),
                    "opening_stock":  dec(r.get("OP_BAL")),
                    "current_stock":  dec(r.get("CUR_STK")),
                    "min_stock":      dec(r.get("RE_QTY")),
                    "is_active":      s(r.get("ACTIVE")) != "N",
                }
                _, new = Product.objects.get_or_create(name=name, defaults=defaults)
                if new:
                    created += 1
                else:
                    skipped += 1
        self.stdout.write(self.style.SUCCESS(f"  OK {created} created, {skipped} already existed\n"))

    # ── GST INVOICES ─────────────────────────────────────────
    def import_invoices(self, clear=False):
        from masters.models import Customer, Product
        from sales.models import SalesInvoice, SalesInvoiceItem

        bill_rows = open_dbf(self.path, "G_BILL.DBF")
        item_rows = open_dbf(self.path, "P_master.DBF")
        self.stdout.write(f"[Invoices]  {len(bill_rows)} bills in G_BILL.DBF, {len(item_rows)} items in P_master.DBF")

        if clear:
            SalesInvoice.objects.filter(invoice_type="gst").delete()

        # customer map: CCODE -> Customer
        cust_map = self._cust_map()
        prod_map = self._prod_map()

        # Group items by BILL_NO
        items_by_bill = {}
        for r in item_rows:
            key = s(r.get("BILL_NO"))
            items_by_bill.setdefault(key, []).append(r)

        created = skipped = no_cust = 0
        with transaction.atomic():
            for r in bill_rows:
                bill_no   = s(r.get("BILL_NO"))
                inv_no    = f"GST{bill_no}"

                if SalesInvoice.objects.filter(invoice_number=inv_no).exists():
                    skipped += 1
                    continue

                # Match customer by CCODE (not CODE)
                p_code   = s(r.get("P_CODE"))   # e.g. "C008"
                customer = cust_map.get(p_code)

                if not customer:
                    # Try creating from embedded CNAME in bill row
                    cname  = s(r.get("CNAME"))
                    gst_no = s(r.get("GST_NO"))
                    if cname:
                        customer, _ = Customer.objects.get_or_create(
                            name=cname,
                            defaults={"gstin": gst_no, "state": s(r.get("STNAME")), "opening_balance": 0}
                        )
                        cust_map[p_code] = customer
                    else:
                        no_cust += 1
                        continue

                inv_date  = d(r.get("B_DATE")) or datetime.date.today()
                subtotal  = dec(r.get("AMOUNT"))
                tax_amt   = dec(r.get("GST_AMT"))
                dis_amt   = dec(r.get("DIS_AMT"))
                net_amt   = dec(r.get("N_AMOUNT"))
                paid      = s(r.get("PMT_RCD")) == "Y"
                amt_rcd   = dec(r.get("AMT_RCD"))

                invoice = SalesInvoice.objects.create(
                    invoice_number  = inv_no,
                    invoice_type    = "gst",
                    customer        = customer,
                    invoice_date    = inv_date,
                    due_date        = None,
                    gr_number       = s(r.get("GR_NO")),
                    gr_date         = d(r.get("GR_DT")),
                    order_number    = s(r.get("ORD_NO")),
                    order_date      = d(r.get("ORD_DT")),
                    vehicle_number  = s(r.get("VEHI_NO")),
                    transport       = s(r.get("TRANS")),
                    despatched_to   = s(r.get("DESP")),
                    notes           = s(r.get("REMK")),
                    place_of_supply = s(r.get("STNAME")),
                    subtotal        = subtotal,
                    tax_amount      = tax_amt,
                    discount        = dis_amt,
                    total_amount    = net_amt,
                    net_rounded     = int(round(float(net_amt))),
                    status          = "paid" if paid else "pending",
                    paid_amount     = amt_rcd if paid else Decimal("0"),
                )

                # Add line items
                for ir in items_by_bill.get(bill_no, []):
                    i_code    = s(ir.get("I_CODE"))
                    product   = prod_map.get(i_code)
                    particular = s(ir.get("PARTICULAR"))

                    if not product:
                        prod_name = particular[:100] if particular else (f"Item-{i_code}" if i_code else None)
                        if not prod_name:
                            continue
                        product, _ = Product.objects.get_or_create(
                            name=prod_name,
                            defaults={"code": i_code or prod_name[:20], "sale_price": dec(ir.get("RATE"))}
                        )
                        prod_map[i_code] = product

                    qty    = dec(ir.get("QTY"), 1)
                    rate   = dec(ir.get("RATE"))
                    gst    = dec(ir.get("GST"))
                    amount = qty * rate
                    tax_a  = amount * gst / 100

                    SalesInvoiceItem.objects.create(
                        invoice   = invoice,
                        product   = product,
                        hsn_no    = s(ir.get("HS_CODE")),
                        unit      = s(ir.get("UNIT")),
                        quantity  = qty,
                        rate      = rate,
                        tax_rate  = gst,
                        tax_amount= tax_a,
                        amount    = amount,
                    )
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"  OK {created} invoices created, {skipped} already existed, {no_cust} skipped (no customer match)\n"
        ))

    # ── PURCHASE BILLS ───────────────────────────────────────
    def import_purchases(self, clear=False):
        from masters.models import Vendor
        from purchase.models import PurchaseBill

        rows = open_dbf(self.path, "GST_PUR.DBF")
        self.stdout.write(f"[Purchases]  {len(rows)} records in GST_PUR.DBF")

        if clear:
            PurchaseBill.objects.all().delete()

        vendor_map = self._vendor_map()
        created = skipped = no_vendor = 0

        with transaction.atomic():
            for r in rows:
                pur_no = f"PUR{s(r.get('GPUR_NO'))}"
                if PurchaseBill.objects.filter(bill_number=pur_no).exists():
                    skipped += 1
                    continue

                p_code = s(r.get("P_CODE"))
                vendor = vendor_map.get(p_code)
                if not vendor:
                    no_vendor += 1
                    continue

                bill_date = d(r.get("B_DATE")) or d(r.get("DATE")) or datetime.date.today()
                subtotal  = dec(r.get("AMOUNT"))
                tax_amt   = dec(r.get("TAX_AMT"))
                dis_amt   = dec(r.get("DIS_AMT"))
                net_amt   = dec(r.get("N_AMOUNT"))

                PurchaseBill.objects.create(
                    bill_number  = pur_no,
                    vendor       = vendor,
                    bill_date    = bill_date,
                    due_date     = d(r.get("DUE_DT")),
                    subtotal     = subtotal,
                    tax_amount   = tax_amt,
                    discount     = dis_amt,
                    total_amount = net_amt,
                    notes        = f"VFP Bill No: {s(r.get('BILL_NO'))}",
                    status       = "paid" if s(r.get("PMT_MAD")) == "Y" else "pending",
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"  OK {created} created, {skipped} already existed, {no_vendor} skipped (no vendor match)\n"
        ))
