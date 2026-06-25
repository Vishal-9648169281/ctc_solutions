from masters.models import Product
updated = 0
for p in Product.objects.all():
    if p.current_stock == 0:
        p.current_stock = p.opening_stock
        p.save()
        updated += 1

print("Updated " + str(updated) + " products with baseline current_stock")
