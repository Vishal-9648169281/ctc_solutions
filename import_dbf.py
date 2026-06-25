# DBF Import Script for CTC Solution ERP
# Run: python import_dbf.py <path_to_zip_or_folder>
import os, sys, zipfile, tempfile, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctc_solution.settings')
django.setup()

from masters.models import Customer, Vendor, Product, Unit, Category, GSTStateCode

try:
    import dbfread
except ImportError:
    print("Installing dbfread...")
    os.system("pip install dbfread")
    import dbfread

def read_dbf(folder, filename):
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        # try uppercase
        path = os.path.join(folder, filename.upper())
    if not os.path.exists(path):
        print(f"  [SKIP] {filename} not found")
        return []
    try:
        t = dbfread.DBF(path, encoding='latin-1', ignore_missing_memofile=True)
        return list(t)
    except Exception as e:
        print(f"  [ERROR] {filename}: {e}")
        return []

def s(val, default=''):
    """Safe string"""
    if val is None:
        return default
    return str(val).strip()

def import_data(folder):
    # ── 1. GST States ─────────────────────────────────────────────
    print("\n--- Importing GST States ---")
    states = read_dbf(folder, 'GSTATE.DBF')
    created = 0
    for r in states:
        code = s(r.get('GNAME'))
        name = s(r.get('STNAME'))
        if code and name:
            obj, c = GSTStateCode.objects.get_or_create(
                state_code=code,
                defaults={'state_name': name}
            )
            if c:
                created += 1
    print(f"  GST States: {created} created, {len(states)-created} skipped")

    # ── 2. Units ──────────────────────────────────────────────────
    print("\n--- Importing Units ---")
    units = read_dbf(folder, 'unit.DBF')
    created = 0
    for r in units:
        name = s(r.get('NAME'))
        if name:
            obj, c = Unit.objects.get_or_create(name=name)
            if c:
                created += 1
    # Also collect units from items
    items = read_dbf(folder, 'item.DBF')
    for r in items:
        name = s(r.get('UNIT'))
        if name:
            Unit.objects.get_or_create(name=name)
    print(f"  Units: done")

    # ── 3. Categories ─────────────────────────────────────────────
    print("\n--- Importing Categories ---")
    cats = read_dbf(folder, 'category.DBF')
    created = 0
    for r in cats:
        name = s(r.get('NAME'))
        if name:
            obj, c = Category.objects.get_or_create(name=name)
            if c:
                created += 1
    print(f"  Categories: {created} created")

    # ── 4. Products/Items ─────────────────────────────────────────
    print("\n--- Importing Products ---")
    created = 0
    skipped = 0
    for r in items:
        code = s(r.get('I_CODE'))
        name = s(r.get('I_NAME'))
        if not name:
            skipped += 1
            continue
        unit_name = s(r.get('UNIT'))
        unit_obj = Unit.objects.filter(name=unit_name).first() if unit_name else None

        obj, c = Product.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'unit': unit_obj,
                'hsn_code': s(r.get('HS_CODE')),
                'purchase_price': float(r.get('PRATE') or 0),
                'sale_price': float(r.get('RATE') or 0),
                'tax_percent': float(r.get('GS_RT') or 0),
                'company': s(r.get('COMP_NAME')),
                'opening_stock': float(r.get('CUR_STK') or 0),
            }
        )
        if c:
            created += 1
        else:
            skipped += 1
    print(f"  Products: {created} created, {skipped} skipped/existing")

    # ── 5. Customers ──────────────────────────────────────────────
    print("\n--- Importing Customers ---")
    customers = read_dbf(folder, 'cust_mst.DBF')
    created = 0
    skipped = 0
    for r in customers:
        name = s(r.get('CNAME'))
        code = s(r.get('CCODE') or r.get('CODE'))
        if not name:
            skipped += 1
            continue
        addr = ' '.join(filter(None, [
            s(r.get('CADD1')), s(r.get('CADD2')), s(r.get('CADD3'))
        ]))
        gst_type = 'W' if s(r.get('CSTAT')) == 'W' else 'I'
        obj, c = Customer.objects.get_or_create(
            name=name,
            defaults={
                'phone': s(r.get('CPHNO'))[:15],
                'email': s(r.get('E_MAIL')),
                'address': addr,
                'gstin': s(r.get('GST_NO')),
                'city': s(r.get('CADD3')),
                'state': s(r.get('STNAME')),
            }
        )
        if c:
            created += 1
        else:
            skipped += 1
    print(f"  Customers: {created} created, {skipped} skipped/existing")

    # ── 6. Vendors (from P_master if available) ───────────────────
    print("\n--- Importing Vendors ---")
    vendors = read_dbf(folder, 'P_master.DBF')
    if not vendors:
        # fallback: use customer file with vendor codes
        vendors = [r for r in customers if s(r.get('VEND_CODE'))]
    created = 0
    skipped = 0
    for r in vendors:
        name = s(r.get('CNAME') or r.get('PNAME') or r.get('NAME'))
        if not name:
            skipped += 1
            continue
        addr = ' '.join(filter(None, [
            s(r.get('CADD1') or r.get('PADD1')),
            s(r.get('CADD2') or r.get('PADD2')),
            s(r.get('CADD3') or r.get('PADD3')),
        ]))
        gst_type = 'W' if s(r.get('CSTAT')) == 'W' else 'I'
        obj, c = Vendor.objects.get_or_create(
            name=name,
            defaults={
                'phone': s(r.get('CPHNO') or r.get('PPHNO'))[:15],
                'email': s(r.get('E_MAIL')),
                'address': addr,
                'gstin': s(r.get('GST_NO')),
                'city': s(r.get('CADD3') or r.get('PADD3')),
            }
        )
        if c:
            created += 1
        else:
            skipped += 1
    print(f"  Vendors: {created} created, {skipped} skipped/existing")

    print("\nImport complete!")
    print(f"  Customers : {Customer.objects.count()}")
    print(f"  Vendors   : {Vendor.objects.count()}")
    print(f"  Products  : {Product.objects.count()}")
    print(f"  Units     : {Unit.objects.count()}")

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Arpit\OneDrive\Desktop\call_mst.zip"

    if src.lower().endswith('.zip'):
        print(f"Extracting {src}...")
        tmpdir = tempfile.mkdtemp()
        with zipfile.ZipFile(src, 'r') as z:
            z.extractall(tmpdir)
        folder = tmpdir
    else:
        folder = src

    print(f"Reading DBF files from: {folder}")
    import_data(folder)
