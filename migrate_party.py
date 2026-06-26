from masters.models import Customer, Vendor, Party
from masters.views import generate_alpha_code

count_c = 0
for c in Customer.objects.all():
    if not Party.objects.filter(legacy_customer_id=c.id).exists():
        Party.objects.create(
            code=generate_alpha_code(Party, c.name),
            name=c.name,
            address=getattr(c, "address", "") or "",
            city=getattr(c, "city", "") or "",
            email=getattr(c, "email", "") or "",
            mobile_number=getattr(c, "phone", "") or "",
            account_type="SD",
            gst_number=getattr(c, "gstin", "") or "",
            opening_balance=getattr(c, "opening_balance", 0) or 0,
            is_active=getattr(c, "is_active", True),
            legacy_customer_id=c.id,
        )
        count_c += 1

print("Migrated " + str(count_c) + " customers to Party")

count_v = 0
for v in Vendor.objects.all():
    if not Party.objects.filter(legacy_vendor_id=v.id).exists():
        Party.objects.create(
            code=generate_alpha_code(Party, v.name),
            name=v.name,
            address=getattr(v, "address", "") or "",
            city=getattr(v, "city", "") or "",
            email=getattr(v, "email", "") or "",
            mobile_number=getattr(v, "phone", "") or "",
            account_type="SC",
            gst_number=getattr(v, "gstin", "") or "",
            opening_balance=getattr(v, "opening_balance", 0) or 0,
            is_active=getattr(v, "is_active", True),
            legacy_vendor_id=v.id,
        )
        count_v += 1

print("Migrated " + str(count_v) + " vendors to Party")
print("Total Parties now: " + str(Party.objects.count()))
