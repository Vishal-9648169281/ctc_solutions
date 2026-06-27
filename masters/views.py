from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Customer, Vendor, Product, Category, Unit, UserProfile, CompanyMaster, SalesmanMaster, AreaMaster, GSTStateCode, GSTMaster, GeneralLedgerMaster, Party
from .middleware import get_user_role, role_required

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password!')
    return render(request, 'registration/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    import json, datetime
    from django.db.models import Sum, Count, Q
    from django.db.models.functions import TruncMonth

    role = get_user_role(request.user)
    total_customers = Customer.objects.filter(is_active=True).count()
    total_vendors   = Vendor.objects.filter(is_active=True).count()
    total_products  = Product.objects.filter(is_active=True).count()
    low_stock       = Product.objects.filter(is_active=True, current_stock__lte=models.F('min_stock')).count()

    from sales.models import SalesInvoice
    from purchase.models import PurchaseBill

    recent_invoices = SalesInvoice.objects.select_related('customer').order_by('-invoice_date')[:8]

    # ── Monthly Sales & Purchase (last 12 months) ─────────
    today = datetime.date.today()
    # Build list of 12 months: oldest → newest
    months = []
    for i in range(11, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12; y -= 1
        months.append((y, m))

    def month_label(y, m):
        return datetime.date(y, m, 1).strftime('%b %Y')

    sales_by_month = {
        (r['month'].year, r['month'].month): float(r['total'] or 0)
        for r in SalesInvoice.objects
            .annotate(month=TruncMonth('invoice_date'))
            .values('month')
            .annotate(total=Sum('total_amount'))
    }
    purchase_by_month = {
        (r['month'].year, r['month'].month): float(r['total'] or 0)
        for r in PurchaseBill.objects
            .annotate(month=TruncMonth('bill_date'))
            .values('month')
            .annotate(total=Sum('total_amount'))
    }

    chart_labels  = [month_label(y, m) for y, m in months]
    chart_sales   = [sales_by_month.get((y, m), 0) for y, m in months]
    chart_purchase= [purchase_by_month.get((y, m), 0) for y, m in months]

    # ── Invoice Status counts ──────────────────────────────
    inv_paid    = SalesInvoice.objects.filter(status='paid').count()
    inv_pending = SalesInvoice.objects.filter(status='pending').count()
    inv_partial = SalesInvoice.objects.filter(status='partial').count()

    # ── Top 5 customers by sales ───────────────────────────
    top_customers = (
        SalesInvoice.objects
        .values('customer__name')
        .annotate(total=Sum('total_amount'))
        .order_by('-total')[:5]
    )

    context = {
        'recent_invoices'  : recent_invoices,
        'total_customers'  : total_customers,
        'total_vendors'    : total_vendors,
        'total_products'   : total_products,
        'low_stock'        : low_stock,
        'user_role'        : role,
        'chart_labels'     : json.dumps(chart_labels),
        'chart_sales'      : json.dumps(chart_sales),
        'chart_purchase'   : json.dumps(chart_purchase),
        'inv_paid'         : inv_paid,
        'inv_pending'      : inv_pending,
        'inv_partial'      : inv_partial,
        'top_customers'    : top_customers,
        'total_sales_amt'  : sum(chart_sales),
        'total_purch_amt'  : sum(chart_purchase),
    }
    return render(request, 'dashboard.html', context)

# ─── USER MANAGEMENT (Admin Only) ───────────────────────
@login_required
@role_required('admin')
def user_list(request):
    users = User.objects.all().order_by('username')
    active_count = users.filter(is_active=True).count()
    blocked_count = users.filter(is_active=False).count()
    admin_count = users.filter(is_superuser=True).count()
    return render(request, 'masters/user_list.html', {
        'users': users,
        'active_count': active_count,
        'blocked_count': blocked_count,
        'admin_count': admin_count,
    })
@login_required
@role_required('admin')
def user_add(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST.get('email', '')
        role = request.POST.get('role', 'sales')
        phone = request.POST.get('phone', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            UserProfile.objects.create(user=user, role=role, phone=phone)
            messages.success(request, f'User {username} created successfully!')
            return redirect('user_list')
    return render(request, 'masters/user_form.html', {'title': 'Add User'})

@login_required
@role_required('admin')
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    try:
        profile = user.profile
    except:
        profile = UserProfile.objects.create(user=user, role='sales')
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        profile.role = request.POST.get('role', 'sales')
        profile.phone = request.POST.get('phone', '')
        profile.save()
        if request.POST.get('password'):
            user.set_password(request.POST['password'])
            user.save()
        messages.success(request, 'User updated successfully!')
        return redirect('user_list')
    return render(request, 'masters/user_form.html', {
        'title': 'Edit User',
        'obj': user,
        'profile': profile,
    })

@login_required
@role_required('admin')
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'Cannot delete your own account!')
    else:
        user.delete()
        messages.success(request, 'User deleted!')
    return redirect('user_list')

# ─── CATEGORY ───────────────────────────────────────────
@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'masters/simple_master.html', {
        'title': 'CATEGORY MASTER',
        'objects': categories,
        'show_code': False,
        'save_url': '/masters/categories/add/',
        'delete_url_base': '/masters/categories/delete/0/',
    })

@login_required
def category_add(request):
    if request.method == 'POST':
        Category.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description', '')
        )
        messages.success(request, 'Category added!')
        return redirect('category_list')
    return render(request, 'masters/category_form.html', {'title': 'Add Category'})

@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST['name']
        category.description = request.POST.get('description', '')
        category.save()
        messages.success(request, 'Category updated!')
        return redirect('category_list')
    return render(request, 'masters/category_form.html', {'title': 'Edit Category', 'obj': category})

@login_required
def category_delete(request, pk):
    get_object_or_404(Category, pk=pk).delete()
    messages.success(request, 'Category deleted!')
    return redirect('category_list')

# ─── UNIT ───────────────────────────────────────────────
@login_required
def unit_list(request):
    units = Unit.objects.all()
    return render(request, 'masters/simple_master.html', {
        'title': 'UNIT MASTER',
        'objects': units,
        'show_code': False,
        'save_url': '/masters/units/add/',
        'delete_url_base': '/masters/units/delete/0/',
    })

@login_required
def unit_add(request):
    if request.method == 'POST':
        Unit.objects.create(name=request.POST['name'], short_name=request.POST['short_name'])
        messages.success(request, 'Unit added!')
        return redirect('unit_list')
    return render(request, 'masters/unit_form.html', {'title': 'Add Unit'})

@login_required
def unit_edit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        unit.name = request.POST['name']
        unit.short_name = request.POST['short_name']
        unit.save()
        messages.success(request, 'Unit updated!')
        return redirect('unit_list')
    return render(request, 'masters/unit_form.html', {'title': 'Edit Unit', 'obj': unit})

@login_required
def unit_delete(request, pk):
    get_object_or_404(Unit, pk=pk).delete()
    messages.success(request, 'Unit deleted!')
    return redirect('unit_list')

# ─── CUSTOMER ───────────────────────────────────────────
@login_required
def customer_list(request):
    query = request.GET.get('q', '')
    customers = Customer.objects.filter(is_active=True)
    if query:
        customers = customers.filter(name__icontains=query)
    return render(request, 'masters/customer_list.html', {'customers': customers, 'query': query})

@login_required
def customer_add(request):
    if request.method == 'POST':
        Customer.objects.create(
            name=request.POST['name'],
            phone=request.POST['phone'],
            mobile=request.POST.get('mobile', ''),
            email=request.POST.get('email', ''),
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            state=request.POST.get('state', ''),
            pincode=request.POST.get('pincode', ''),
            gstin=request.POST.get('gstin', ''),
            opening_balance=request.POST.get('opening_balance', 0),
        )
        messages.success(request, 'Customer added!')
        return redirect('customer_list')
    return render(request, 'masters/customer_form.html', {'title': 'Add Customer'})

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.name = request.POST['name']
        customer.phone = request.POST['phone']
        customer.mobile = request.POST.get('mobile', '')
        customer.email = request.POST.get('email', '')
        customer.address = request.POST.get('address', '')
        customer.city = request.POST.get('city', '')
        customer.state = request.POST.get('state', '')
        customer.pincode = request.POST.get('pincode', '')
        customer.gstin = request.POST.get('gstin', '')
        customer.opening_balance = request.POST.get('opening_balance', 0)
        customer.save()
        messages.success(request, 'Customer updated!')
        return redirect('customer_list')
    return render(request, 'masters/customer_form.html', {'title': 'Edit Customer', 'obj': customer})

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.is_active = False
    customer.save()
    messages.success(request, 'Customer deleted!')
    return redirect('customer_list')

# ─── VENDOR ─────────────────────────────────────────────
@login_required
def vendor_list(request):
    query = request.GET.get('q', '')
    vendors = Vendor.objects.filter(is_active=True)
    if query:
        vendors = vendors.filter(name__icontains=query)
    return render(request, 'masters/vendor_list.html', {'vendors': vendors, 'query': query})

@login_required
def vendor_add(request):
    if request.method == 'POST':
        Vendor.objects.create(
            name=request.POST['name'],
            phone=request.POST['phone'],
            mobile=request.POST.get('mobile', ''),
            email=request.POST.get('email', ''),
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            state=request.POST.get('state', ''),
            pincode=request.POST.get('pincode', ''),
            gstin=request.POST.get('gstin', ''),
            opening_balance=request.POST.get('opening_balance', 0),
        )
        messages.success(request, 'Vendor added!')
        return redirect('vendor_list')
    return render(request, 'masters/vendor_form.html', {'title': 'Add Vendor'})

@login_required
def vendor_edit(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        vendor.name = request.POST['name']
        vendor.phone = request.POST['phone']
        vendor.mobile = request.POST.get('mobile', '')
        vendor.email = request.POST.get('email', '')
        vendor.address = request.POST.get('address', '')
        vendor.city = request.POST.get('city', '')
        vendor.state = request.POST.get('state', '')
        vendor.pincode = request.POST.get('pincode', '')
        vendor.gstin = request.POST.get('gstin', '')
        vendor.opening_balance = request.POST.get('opening_balance', 0)
        vendor.save()
        messages.success(request, 'Vendor updated!')
        return redirect('vendor_list')
    return render(request, 'masters/vendor_form.html', {'title': 'Edit Vendor', 'obj': vendor})

@login_required
def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    vendor.is_active = False
    vendor.save()
    messages.success(request, 'Vendor deleted!')
    return redirect('vendor_list')

# ─── PRODUCT ────────────────────────────────────────────
@login_required
def product_list(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True).select_related('category', 'unit')
    if query:
        products = products.filter(name__icontains=query)
    return render(request, 'masters/product_list.html', {'products': products, 'query': query})

@login_required
def product_add(request):
    categories = Category.objects.filter(is_active=True)
    units = Unit.objects.filter(is_active=True)
    if request.method == 'POST':
        Product.objects.create(
            name=request.POST['name'],
            code=generate_alpha_code(Product, request.POST['name']),
            company=request.POST.get('company', ''),
            category_id=request.POST.get('category') or None,
            unit_id=request.POST.get('unit') or None,
            purchase_price=request.POST.get('purchase_price', 0),
            sale_price=request.POST.get('sale_price', 0),
            tax_rate=request.POST.get('tax_rate', 18),
            hsn_code=request.POST.get('hsn_code', ''),
            opening_stock=request.POST.get('opening_stock', 0),
            current_stock=request.POST.get('opening_stock', 0),
            min_stock=request.POST.get('min_stock', 0),
        )
        messages.success(request, 'Product added!')
        return redirect('product_list')
    all_companies = list(Product.objects.exclude(company='').values_list('company', flat=True).distinct())
    return render(request, 'masters/product_form.html', {
        'title': 'Add Product', 'categories': categories, 'units': units, 'all_companies': all_companies
    })

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.filter(is_active=True)
    units = Unit.objects.filter(is_active=True)
    if request.method == 'POST':
        product.name = request.POST['name']
        product.code = request.POST['code']
        product.company = request.POST.get('company', '')
        product.category_id = request.POST.get('category') or None
        product.unit_id = request.POST.get('unit') or None
        product.purchase_price = request.POST.get('purchase_price', 0)
        product.sale_price = request.POST.get('sale_price', 0)
        product.tax_rate = request.POST.get('tax_rate', 18)
        product.hsn_code = request.POST.get('hsn_code', '')
        product.min_stock = request.POST.get('min_stock', 0)
        product.save()
        messages.success(request, 'Product updated!')
        return redirect('product_list')
    all_companies = list(Product.objects.exclude(company='').values_list('company', flat=True).distinct())
    return render(request, 'masters/product_form.html', {
        'title': 'Edit Product', 'obj': product,
        'categories': categories, 'units': units, 'all_companies': all_companies
    })

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = False
    product.save()
    messages.success(request, 'Product deleted!')
    return redirect('product_list')
@login_required
@role_required('admin')
def user_block(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'Cannot block your own account!')
    else:
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} blocked!')
    return redirect('user_list')

@login_required
@role_required('admin')
def user_unblock(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save()
    messages.success(request, f'User {user.username} unblocked!')
    return redirect('user_list')
# ─── COMPANY MASTER ─────────────────────────────────────
@login_required
def company_list(request):
    companies = CompanyMaster.objects.all()
    return render(request, 'masters/simple_master.html', {
        'title': 'COMPANY MASTER',
        'objects': companies,
        'show_code': True,
        'save_url': '/masters/company/save/',
        'delete_url_base': '/masters/company/delete/0/',
    })

@login_required
def company_save(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        name = request.POST['name']
        if pk:
            obj = get_object_or_404(CompanyMaster, pk=pk)
            obj.name = name
        else:
            obj = CompanyMaster()
            obj.name = name
            obj.code = generate_alpha_code(CompanyMaster, name)
        obj.save()
        messages.success(request, f'Company saved! Code: {obj.code}')
    return redirect('company_list')

@login_required
def company_delete(request, pk):
    get_object_or_404(CompanyMaster, pk=pk).delete()
    messages.success(request, 'Company deleted!')
    return redirect('company_list')


# ─── SALESMEN MASTER ────────────────────────────────────
@login_required
def salesman_list(request):
    salesmen = SalesmanMaster.objects.all()
    return render(request, 'masters/simple_master.html', {
        'title': 'SALESMEN MASTER',
        'objects': salesmen,
        'show_code': True,
        'save_url': '/masters/salesman/save/',
        'delete_url_base': '/masters/salesman/delete/0/',
    })

@login_required
def salesman_save(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        name = request.POST['name']
        if pk:
            obj = get_object_or_404(SalesmanMaster, pk=pk)
            obj.name = name
        else:
            obj = SalesmanMaster()
            obj.name = name
            obj.code = generate_alpha_code(SalesmanMaster, name)
        obj.save()
        messages.success(request, f'Salesman saved! Code: {obj.code}')
    return redirect('salesman_list')

@login_required
def salesman_delete(request, pk):
    get_object_or_404(SalesmanMaster, pk=pk).delete()
    messages.success(request, 'Salesman deleted!')
    return redirect('salesman_list')


# ─── AREA MASTER ────────────────────────────────────────
@login_required
def area_list(request):
    areas = AreaMaster.objects.all()
    return render(request, 'masters/simple_master.html', {
        'title': 'AREA MASTER',
        'objects': areas,
        'show_code': True,
        'save_url': '/masters/area/save/',
        'delete_url_base': '/masters/area/delete/0/',
    })

@login_required
def area_save(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        name = request.POST['name']
        if pk:
            obj = get_object_or_404(AreaMaster, pk=pk)
            obj.name = name
        else:
            obj = AreaMaster()
            obj.name = name
            obj.code = generate_alpha_code(AreaMaster, name)
        obj.save()
        messages.success(request, f'Area saved! Code: {obj.code}')
    return redirect('area_list')

@login_required
def area_delete(request, pk):
    get_object_or_404(AreaMaster, pk=pk).delete()
    messages.success(request, 'Area deleted!')
    return redirect('area_list')


# ─── GST STATE CODE MASTER ──────────────────────────────
@login_required
def gststate_list(request):
    states = GSTStateCode.objects.all()
    if not states.exists():
        default_states = [
            ('01','JAMMU AND KASHMIR'),('02','HIMACHAL PRADESH'),('03','PUNJAB'),
            ('04','CHANDIGARH'),('05','UTTARAKHAND'),('06','HARYANA'),('07','DELHI'),
            ('08','RAJASTHAN'),('09','UTTAR PRADESH'),('10','BIHAR'),('11','SIKKIM'),
            ('12','ARUNACHAL PRADESH'),('13','NAGALAND'),('14','MANIPUR'),('15','MIZORAM'),
            ('16','TRIPURA'),('17','MEGHALAYA'),('18','ASSAM'),('19','WEST BENGAL'),
            ('20','JHARKHAND'),('21','ODISHA'),('22','CHATTISGARH'),('23','MADHYA PRADESH'),
            ('24','GUJARAT'),('25','DAMAN AND DIU'),('26','DADRA AND NAGAR HAVELI'),
            ('27','MAHARASHTRA'),('28','ANDHRA PRADESH'),('29','KARNATAKA'),('30','GOA'),
            ('31','LAKSHADWEEP'),('32','KERALA'),('33','TAMIL NADU'),('34','PUDUCHERRY'),
            ('35','ANDAMAN AND NICOBAR ISLANDS'),('36','TELANGANA'),('37','ANDHRA PRADESH (NEW)'),
            ('38','LADAKH'),
        ]
        for code, name in default_states:
            GSTStateCode.objects.create(state_code=code, state_name=name)
        states = GSTStateCode.objects.all()
    return render(request, 'masters/gststate_list.html', {'states': states})

@login_required
def gststate_save(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        if pk:
            obj = get_object_or_404(GSTStateCode, pk=pk)
        else:
            obj = GSTStateCode()
        obj.state_code = request.POST['state_code']
        obj.state_name = request.POST['state_name']
        obj.save()
        messages.success(request, 'State saved!')
    return redirect('gststate_list')

@login_required
def gststate_delete(request, pk):
    get_object_or_404(GSTStateCode, pk=pk).delete()
    messages.success(request, 'State deleted!')
    return redirect('gststate_list')


# ─── GST MASTER ─────────────────────────────────────────
@login_required
def gstmaster_list(request):
    records = GSTMaster.objects.all()
    return render(request, 'masters/gstmaster_list.html', {'records': records})

@login_required
def gstmaster_save(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        if pk:
            obj = get_object_or_404(GSTMaster, pk=pk)
        else:
            obj = GSTMaster()
        obj.gst_percent = request.POST.get('gst_percent') or 0
        obj.sale_taxfree_account = request.POST.get('sale_taxfree_account', '')
        obj.sale_gst_account = request.POST.get('sale_gst_account', '')
        obj.sale_within_state_account = request.POST.get('sale_within_state_account', '')
        obj.sale_cgst_account = request.POST.get('sale_cgst_account', '')
        obj.sale_sgst_account = request.POST.get('sale_sgst_account', '')
        obj.sale_interstate_account = request.POST.get('sale_interstate_account', '')
        obj.sale_igst_account = request.POST.get('sale_igst_account', '')
        obj.purchase_taxfree_account = request.POST.get('purchase_taxfree_account', '')
        obj.purchase_gst_account = request.POST.get('purchase_gst_account', '')
        obj.purchase_within_state_account = request.POST.get('purchase_within_state_account', '')
        obj.purchase_cgst_account = request.POST.get('purchase_cgst_account', '')
        obj.purchase_sgst_account = request.POST.get('purchase_sgst_account', '')
        obj.purchase_interstate_account = request.POST.get('purchase_interstate_account', '')
        obj.purchase_igst_account = request.POST.get('purchase_igst_account', '')
        obj.save()
        messages.success(request, 'GST Master saved!')
    return redirect('gstmaster_list')

@login_required
def gstmaster_delete(request, pk):
    get_object_or_404(GSTMaster, pk=pk).delete()
    messages.success(request, 'GST record deleted!')
    return redirect('gstmaster_list')


# ─── GENERAL LEDGER MASTER ──────────────────────────────
@login_required
def ledger_list(request):
    ledgers = GeneralLedgerMaster.objects.all()
    if not ledgers.exists():
        default_ledgers = [
            ('ADVANCE', 'INVESTMENTS'),
            ('CASH DISCOUNT', 'SALES'),
            ('CASH IN HAND', 'CASH & BANK BALANCES'),
            ('CESS', 'SALES'),
            ('COMISSION A/C', 'EXPENSE'),
            ('COMPUTER', 'PURCHASES'),
            ('CYCLE A/C', 'ASSET'),
            ('DIFFERENCE ACCOUNT', 'EXPENSES PAYABLE'),
            ('DISCOUNT A/C', 'MISC EXPENDITURE'),
            ('FREIGHT (INWARD)', 'PURCHASES'),
            ('FRIGHT', 'EXPENSES PAYABLE'),
            ('GST PURCHASE 0%', 'PURCHASES'),
            ('GST PURCHASE 12%', 'PURCHASES'),
            ('GST PURCHASE 18%', 'PURCHASES'),
            ('GST PURCHASE 28%', 'PURCHASES'),
            ('GST PURCHASE 5%', 'PURCHASES'),
            ('GST PURCHASE CGST 14%', 'PURCHASES'),
            ('GST PURCHASE CGST 2.5%', 'PURCHASES'),
            ('GST PURCHASE CGST 6%', 'PURCHASES'),
            ('GST PURCHASE CGST 9%', 'PURCHASES'),
            ('GST PURCHASE IGST 12%', 'PURCHASES'),
            ('GST PURCHASE IGST 18%', 'PURCHASES'),
            ('GST PURCHASE IGST 28%', 'PURCHASES'),
            ('GST PURCHASE IGST 5%', 'PURCHASES'),
            ('GST PURCHASE INTERSTATE', 'PURCHASES'),
            ('GST PURCHASE SGST 14%', 'PURCHASES'),
            ('GST PURCHASE SGST 2.5%', 'PURCHASES'),
            ('GST PURCHASE SGST 6%', 'PURCHASES'),
        ]
        default_ledgers2 = [
            ('ADV001','ADVANCE','EXPENSES_PAYABLE'),
            ('CSH001','CASH DISCOUNT','SALES'),
            ('CSH002','CASH IN HAND','CASH'),
            ('CES001','CESS','DUTIES_TAXES'),
            ('COM001','COMMISSION A/C','EXPENSES_PAYABLE'),
            ('CMP001','COMPUTER','FIXED_ASSETS'),
            ('CYC001','CYCLE A/C','FIXED_ASSETS'),
            ('DIF001','DIFFERENCE ACCOUNT','EXPENSES_PAYABLE'),
            ('DIS001','DISCOUNT A/C','EXPENSES_PAYABLE'),
            ('FRT001','FREIGHT (INWARD)','PURCHASES'),
            ('FRG001','FREIGHT OUTWARD','EXPENSES_PAYABLE'),
            ('GSP000','GST PURCHASE 0%','DUTIES_TAXES'),
            ('GSP005','GST PURCHASE 5%','DUTIES_TAXES'),
            ('GSP012','GST PURCHASE 12%','DUTIES_TAXES'),
            ('GSP018','GST PURCHASE 18%','DUTIES_TAXES'),
            ('GSP028','GST PURCHASE 28%','DUTIES_TAXES'),
            ('GPC025','GST PURCHASE CGST 2.5%','DUTIES_TAXES'),
            ('GPC060','GST PURCHASE CGST 6%','DUTIES_TAXES'),
            ('GPC090','GST PURCHASE CGST 9%','DUTIES_TAXES'),
            ('GPC140','GST PURCHASE CGST 14%','DUTIES_TAXES'),
            ('GPS025','GST PURCHASE SGST 2.5%','DUTIES_TAXES'),
            ('GPS060','GST PURCHASE SGST 6%','DUTIES_TAXES'),
            ('GPS090','GST PURCHASE SGST 9%','DUTIES_TAXES'),
            ('GPS140','GST PURCHASE SGST 14%','DUTIES_TAXES'),
            ('GPI005','GST PURCHASE IGST 5%','DUTIES_TAXES'),
            ('GPI012','GST PURCHASE IGST 12%','DUTIES_TAXES'),
            ('GPI018','GST PURCHASE IGST 18%','DUTIES_TAXES'),
            ('GPI028','GST PURCHASE IGST 28%','DUTIES_TAXES'),
            ('GSPINT','GST PURCHASE INTERSTATE','DUTIES_TAXES'),
            ('GSS000','GST SALES 0%','DUTIES_TAXES'),
            ('GSS005','GST SALES 5%','DUTIES_TAXES'),
            ('GSS012','GST SALES 12%','DUTIES_TAXES'),
            ('GSS018','GST SALES 18%','DUTIES_TAXES'),
            ('GSS028','GST SALES 28%','DUTIES_TAXES'),
            ('GSC025','GST SALES CGST 2.5%','DUTIES_TAXES'),
            ('GSC090','GST SALES CGST 9%','DUTIES_TAXES'),
            ('GSG025','GST SALES SGST 2.5%','DUTIES_TAXES'),
            ('GSG090','GST SALES SGST 9%','DUTIES_TAXES'),
            ('GSI018','GST SALES IGST 18%','DUTIES_TAXES'),
            ('SAL001','SALES ACCOUNT','SALES'),
            ('PUR001','PURCHASE ACCOUNT','PURCHASES'),
            ('CAP001','CAPITAL ACCOUNT','CAPITAL'),
            ('BNK001','BANK ACCOUNT','BANK'),
        ]
        for code, desc, grp in default_ledgers2:
            GeneralLedgerMaster.objects.get_or_create(
                ledger_code=code,
                defaults={'description': desc, 'ledger_group': grp, 'opening_balance': 0}
            )
        ledgers = GeneralLedgerMaster.objects.all()
    return render(request, 'masters/ledger_list.html', {'ledgers': ledgers})

@login_required
def ledger_save(request):
    if request.method == 'POST':
        pk = request.POST.get('pk')
        if pk:
            obj = get_object_or_404(GeneralLedgerMaster, pk=pk)
        else:
            obj = GeneralLedgerMaster()
        obj.description = request.POST.get('description', '').strip()
        obj.ledger_code = request.POST.get('ledger_code', '').strip()
        obj.ledger_group = request.POST.get('ledger_group', 'OTHER')
        obj.opening_balance = request.POST.get('opening_balance') or 0
        obj.save()
        messages.success(request, 'Ledger saved!')
    return redirect('ledger_list')

@login_required
def ledger_delete(request, pk):
    get_object_or_404(GeneralLedgerMaster, pk=pk).delete()
    messages.success(request, 'Ledger deleted!')
    return redirect('ledger_list')


# ─── RATE MODIFICATION ──────────────────────────────────
@login_required
def rate_modification(request):
    products = Product.objects.filter(is_active=True)
    if request.method == 'POST':
        product_ids = request.POST.getlist('product_id[]')
        new_rates = request.POST.getlist('new_rate[]')
        updated = 0
        for i in range(len(product_ids)):
            if new_rates[i]:
                p = Product.objects.filter(pk=product_ids[i]).first()
                if p:
                    p.sale_price = new_rates[i]
                    p.save()
                    updated += 1
        messages.success(request, f'{updated} product rates updated!')
        return redirect('rate_modification')
    return render(request, 'masters/rate_modification.html', {'products': products})


def _indian_rupees(amount):
    """Convert number to Indian spoken format: 5 lakh 90 thousand 500"""
    amount = int(amount)
    if amount == 0:
        return "zero rupees"
    parts = []
    crore   = amount // 10000000; amount %= 10000000
    lakh    = amount // 100000;   amount %= 100000
    thousand= amount // 1000;     amount %= 1000
    hundred = amount // 100;      amount %= 100
    if crore:    parts.append(f"{crore} crore")
    if lakh:     parts.append(f"{lakh} lakh")
    if thousand: parts.append(f"{thousand} thousand")
    if hundred:  parts.append(f"{hundred} hundred")
    if amount:   parts.append(str(amount))
    return "rupees " + " ".join(parts)


# ─── VOICE ASSISTANT ────────────────────────────────────
@login_required
def voice_assistant(request):
    import datetime
    from django.db.models import Sum, Max, Q
    from sales.models import SalesInvoice
    from difflib import get_close_matches

    query = request.GET.get('q', '').strip().lower()
    if not query:
        return JsonResponse({'speak': 'Yes, I am listening. Please ask your question.', 'action': None})

    today = datetime.date.today()
    role = get_user_role(request.user)
    can_see_amounts = request.user.is_superuser or role in ('admin', 'owner', 'accounts', 'manager')
    DENIED = {'speak': 'Sorry, only admin and owner are authorized to view financial information.', 'action': None}

    # ── today's highest sale ──────────────────────────────
    if any(k in query for k in ['highest sale', 'maximum sale', 'biggest sale', 'top sale', 'sabse bada', 'highest invoice']):
        if not can_see_amounts:
            return JsonResponse(DENIED)
        scope = 'today' if 'today' in query else ('month' if 'month' in query else 'today')
        if scope == 'today':
            inv = SalesInvoice.objects.filter(invoice_date=today).order_by('-total_amount').first()
            label = 'today'
        else:
            inv = SalesInvoice.objects.filter(invoice_date__month=today.month, invoice_date__year=today.year).order_by('-total_amount').first()
            label = 'this month'
        if inv:
            return JsonResponse({
                'speak': f"Highest sale {label} is invoice {inv.invoice_number} of {inv.customer.name} for {_indian_rupees(inv.total_amount)}.",
                'action': f'/sales/invoices/{inv.pk}/',
            })
        return JsonResponse({'speak': f'No sales found for {label}.', 'action': None})

    # ── total sales today / this month ───────────────────
    if any(k in query for k in ['total sale', 'kitni sale', 'sales today', 'aaj ki sale', 'total invoice', 'total amount']):
        if not can_see_amounts:
            return JsonResponse(DENIED)
        if 'month' in query:
            total = SalesInvoice.objects.filter(invoice_date__month=today.month, invoice_date__year=today.year).aggregate(t=Sum('total_amount'))['t'] or 0
            count = SalesInvoice.objects.filter(invoice_date__month=today.month, invoice_date__year=today.year).count()
            return JsonResponse({'speak': f'This month total sales are {_indian_rupees(total)} across {count} invoices.', 'action': '/sales/invoices/'})
        else:
            total = SalesInvoice.objects.filter(invoice_date=today).aggregate(t=Sum('total_amount'))['t'] or 0
            count = SalesInvoice.objects.filter(invoice_date=today).count()
            return JsonResponse({'speak': f"Today's total sales are {_indian_rupees(total)} across {count} invoices.", 'action': '/sales/invoices/?from_date=' + str(today) + '&to_date=' + str(today)})

    # ── pending invoices ──────────────────────────────────
    if any(k in query for k in ['pending', 'unpaid', 'baaki', 'due']):
        count = SalesInvoice.objects.filter(status='pending').count()
        if can_see_amounts:
            total = SalesInvoice.objects.filter(status='pending').aggregate(t=Sum('total_amount'))['t'] or 0
            return JsonResponse({'speak': f'There are {count} pending invoices totaling {_indian_rupees(total)}.', 'action': '/sales/invoices/'})
        return JsonResponse({'speak': f'There are {count} pending invoices.', 'action': '/sales/invoices/'})

    # ── how many invoices today ───────────────────────────
    if any(k in query for k in ['how many invoice', 'kitne invoice', 'count invoice', 'invoice today', 'aaj ke invoice']):
        count = SalesInvoice.objects.filter(invoice_date=today).count()
        return JsonResponse({'speak': f"Today {count} invoice{'s' if count != 1 else ''} ha{'ve' if count != 1 else 's'} been created.", 'action': '/sales/invoices/?from_date=' + str(today) + '&to_date=' + str(today)})

    # ── show bill / invoice of [customer] ─────────────────
    for kw in ['show bill of', 'show invoice of', 'bill of', 'invoice of', 'find bill', 'search bill', 'bill for', 'invoice for', 'ka bill', 'ki invoice']:
        if kw in query:
            cname = query.split(kw, 1)[-1].strip()
            if cname:
                from masters.models import Customer
                all_names = list(Customer.objects.filter(is_active=True).values_list('name', flat=True))
                matches = get_close_matches(cname.upper(), [n.upper() for n in all_names], n=1, cutoff=0.4)
                if matches:
                    matched_name = all_names[[n.upper() for n in all_names].index(matches[0])]
                    cust = Customer.objects.filter(name=matched_name).first()
                    inv = SalesInvoice.objects.filter(customer=cust).order_by('-invoice_date').first()
                    if inv:
                        if can_see_amounts:
                            msg = f"Last invoice of {cust.name} is {inv.invoice_number} dated {inv.invoice_date} for {_indian_rupees(inv.total_amount)}."
                        else:
                            msg = f"Last invoice of {cust.name} is {inv.invoice_number} dated {inv.invoice_date}."
                        return JsonResponse({'speak': msg, 'action': f'/sales/invoices/{inv.pk}/'})
                    return JsonResponse({'speak': f'No invoice found for {cust.name}.', 'action': None})
                return JsonResponse({'speak': f'No customer found matching {cname}. Please check the name.', 'action': None})

    # ── customer balance ──────────────────────────────────
    if any(k in query for k in ['balance of', 'outstanding', 'kitna baaki', 'balance for']):
        if not can_see_amounts:
            return JsonResponse(DENIED)
        for kw in ['balance of', 'balance for', 'outstanding of']:
            if kw in query:
                cname = query.split(kw, 1)[-1].strip()
                from masters.models import Customer
                all_names = list(Customer.objects.filter(is_active=True).values_list('name', flat=True))
                matches = get_close_matches(cname.upper(), [n.upper() for n in all_names], n=1, cutoff=0.4)
                if matches:
                    matched_name = all_names[[n.upper() for n in all_names].index(matches[0])]
                    cust = Customer.objects.filter(name=matched_name).first()
                    total_due = SalesInvoice.objects.filter(customer=cust).exclude(status='paid').aggregate(t=Sum('total_amount'))['t'] or 0
                    paid = SalesInvoice.objects.filter(customer=cust).aggregate(t=Sum('paid_amount'))['t'] or 0
                    balance = total_due - paid
                    return JsonResponse({'speak': f"{cust.name} has outstanding balance of {_indian_rupees(balance)}.", 'action': f'/masters/customers/'})
                return JsonResponse({'speak': f'Customer {cname} not found.', 'action': None})

    # ── what time / what day ──────────────────────────────
    if any(k in query for k in ['what time', 'time now', 'current time', 'kitna baja', 'time kya']):
        now = datetime.datetime.now()
        t = now.strftime('%I:%M %p').lstrip('0')
        return JsonResponse({'speak': f'The current time is {t}.', 'action': None})

    if any(k in query for k in ['what day', 'which day', 'aaj kya', 'today date', 'what is today', 'todays date', "today's date"]):
        day = today.strftime('%A, %d %B %Y')
        return JsonResponse({'speak': f'Today is {day}.', 'action': None})

    # ── greetings ─────────────────────────────────────────
    uname = request.user.first_name or request.user.username
    if any(k in query for k in ['hello', 'hi ', 'hey', 'hii', 'namaste', 'namaskar']):
        h = datetime.datetime.now().hour
        greet = 'Good morning' if h < 12 else ('Good afternoon' if h < 17 else 'Good evening')
        return JsonResponse({'speak': f'{greet}, {uname}! I am your CTC voice assistant. How can I help you today?', 'action': None})

    # ── invoice lookup by number ──────────────────────────
    for kw in ['invoice', 'bill number', 'inv']:
        if kw in query:
            # extract alphanumeric token after keyword
            import re
            raw = query.split(kw, 1)[-1].strip()
            # convert spoken digits to numbers: "five five six" → "556"
            word_nums = {'zero':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9'}
            for w,d in word_nums.items():
                raw = raw.replace(w, d)
            token = re.sub(r'[^a-z0-9]', '', raw.lower())
            if token:
                # fuzzy search in invoice numbers
                all_invs = list(SalesInvoice.objects.all().values_list('invoice_number', flat=True))
                norm = [n.lower().replace('-','').replace('/','') for n in all_invs]
                matches_i = [i for i,n in enumerate(norm) if token in n or n in token]
                if not matches_i:
                    matches_i = [i for i,n in enumerate(norm) if any(c in n for c in token)]
                if matches_i:
                    inv = SalesInvoice.objects.get(invoice_number=all_invs[matches_i[0]])
                    creator = inv.created_by.get_full_name() or inv.created_by.username if inv.created_by else 'unknown'
                    created_time = inv.created_at.strftime('%d %B %Y at %I:%M %p') if inv.created_at else 'unknown time'
                    if can_see_amounts:
                        msg = (f"Invoice {inv.invoice_number} is for customer {inv.customer.name}, "
                               f"amount {_indian_rupees(inv.total_amount)}, status {inv.status}, "
                               f"created by {creator} on {created_time}.")
                    else:
                        msg = (f"Invoice {inv.invoice_number} is for customer {inv.customer.name}, "
                               f"status {inv.status}, created by {creator} on {created_time}.")
                    return JsonResponse({'speak': msg, 'action': f'/sales/invoices/{inv.pk}/'})
            break

    # ── go to page ────────────────────────────────────────
    nav_map = [
        (['dashboard', 'home', 'ghar'], '/dashboard/', 'Opening dashboard.'),
        (['invoice list', 'all invoice', 'sales list', 'invoice dekho'], '/sales/invoices/', 'Opening invoice list.'),
        (['new invoice', 'add invoice', 'create invoice', 'naya bill'], '/sales/invoices/add/?type=gst', 'Opening new invoice form.'),
        (['customer list', 'customer master', 'khata list'], '/masters/customers/', 'Opening customer list.'),
        (['product', 'item list'], '/masters/products/', 'Opening product list.'),
        (['purchase', 'bill list'], '/purchase/bills/', 'Opening purchase bills.'),
        (['payment', 'receive payment'], '/payments/receive/', 'Opening receive payment.'),
        (['user management', 'staff list'], '/users/', 'Opening user management.'),
    ]
    for keywords, url, msg in nav_map:
        if any(k in query for k in keywords):
            return JsonResponse({'speak': msg, 'action': url})

    return JsonResponse({'speak': f"Sorry {uname}, I did not understand that. Try saying: today highest sale, total sales today, what time is it, or show bill of customer name.", 'action': None})


def generate_alpha_code(model_class, name):
    """Generate code like V001, V002 based on first letter of name"""
    if not name:
        return 'X001'
    first_letter = name.strip()[0].upper()
    existing = model_class.objects.filter(code__istartswith=first_letter).order_by('-code')
    max_num = 0
    for obj in existing:
        try:
            num_part = obj.code[1:]
            num = int(num_part)
            if num > max_num:
                max_num = num
        except (ValueError, IndexError):
            continue
    new_num = max_num + 1
    return f"{first_letter}{new_num:03d}"


# ─── QUICK-ADD AJAX VIEWS ─────────────────────────────────────────────────────
# Used by invoice / bill forms to add customer/vendor/product without leaving the form

@login_required
@require_POST
def quick_add_customer(request):
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'Name is required'})
    obj, created = Customer.objects.get_or_create(
        name=name,
        defaults={
            'phone': request.POST.get('phone', ''),
            'gstin': request.POST.get('gstin', ''),
            'address': request.POST.get('address', ''),
            'city': request.POST.get('city', ''),
            'state': request.POST.get('state', ''),
            'opening_balance': 0,
            'is_active': True,
        }
    )
    return JsonResponse({'ok': True, 'pk': obj.pk, 'name': obj.name, 'created': created})


@login_required
@require_POST
def quick_add_vendor(request):
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'Name is required'})
    obj, created = Vendor.objects.get_or_create(
        name=name,
        defaults={
            'phone': request.POST.get('phone', ''),
            'gstin': request.POST.get('gstin', ''),
            'address': request.POST.get('address', ''),
            'city': request.POST.get('city', ''),
            'state': request.POST.get('state', ''),
            'opening_balance': 0,
            'is_active': True,
        }
    )
    return JsonResponse({'ok': True, 'pk': obj.pk, 'name': obj.name, 'created': created})


@login_required
@require_POST
def quick_add_product(request):
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': 'Name is required'})
    # Auto-generate a unique code
    import re
    base_code = re.sub(r'[^A-Z0-9]', '', name.upper())[:8] or 'PROD'
    code = base_code
    counter = 1
    while Product.objects.filter(code=code).exists():
        code = f"{base_code}{counter}"
        counter += 1
    sale_price = request.POST.get('sale_price', 0) or 0
    tax_rate = request.POST.get('tax_rate', 18) or 18
    hsn_code = request.POST.get('hsn_code', '')
    unit_name = request.POST.get('unit', 'NOS')
    unit_obj, _ = Unit.objects.get_or_create(name=unit_name, defaults={'short_name': unit_name[:10]})
    obj = Product.objects.create(
        name=name, code=code,
        sale_price=sale_price, purchase_price=0,
        tax_rate=int(tax_rate), hsn_code=hsn_code,
        unit=unit_obj, is_active=True,
    )
    return JsonResponse({
        'ok': True, 'pk': obj.pk, 'name': obj.name,
        'sale_price': float(obj.sale_price),
        'tax_rate': obj.tax_rate,
        'hsn_code': obj.hsn_code,
        'unit': unit_obj.short_name,
    })



# ─── PARTY MASTER ───────────────────────────────────────
@login_required
def party_list(request):
    query = request.GET.get('q', '')
    parties = Party.objects.filter(is_active=True)
    if query:
        parties = parties.filter(name__icontains=query)
    return render(request, 'masters/party_list.html', {'parties': parties, 'query': query})

@login_required
def party_add(request):
    states = GSTStateCode.objects.all()
    if request.method == 'POST':
        party = Party(
            code=generate_alpha_code(Party, request.POST['name']),
            name=request.POST['name'],
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            email=request.POST.get('email', ''),
            contact_person=request.POST.get('contact_person', ''),
            mobile_number=request.POST.get('mobile_number', ''),
            account_type=request.POST.get('account_type', 'SD'),
            gst_number=request.POST.get('gst_number', ''),
            gst_registration_type=request.POST.get('gst_registration_type', 'unregistered'),
            state_id=request.POST.get('state') or None,
            gst_type=request.POST.get('gst_type', 'W'),
            amc_start_date=request.POST.get('amc_start_date') or None,
            amc_end_date=request.POST.get('amc_end_date') or None,
            opening_balance=request.POST.get('opening_balance') or 0,
        )
        party.save()
        messages.success(request, f'Party {party.name} created with code {party.code}!')
        return redirect('party_list')
    return render(request, 'masters/party_form.html', {'states': states, 'party': None})

@login_required
def party_edit(request, pk):
    party = get_object_or_404(Party, pk=pk)
    states = GSTStateCode.objects.all()
    if request.method == 'POST':
        party.name = request.POST['name']
        party.address = request.POST.get('address', '')
        party.city = request.POST.get('city', '')
        party.email = request.POST.get('email', '')
        party.contact_person = request.POST.get('contact_person', '')
        party.mobile_number = request.POST.get('mobile_number', '')
        party.account_type = request.POST.get('account_type', 'SD')
        party.gst_number = request.POST.get('gst_number', '')
        party.gst_registration_type = request.POST.get('gst_registration_type', 'unregistered')
        party.state_id = request.POST.get('state') or None
        party.gst_type = request.POST.get('gst_type', 'W')
        party.amc_start_date = request.POST.get('amc_start_date') or None
        party.amc_end_date = request.POST.get('amc_end_date') or None
        party.opening_balance = request.POST.get('opening_balance') or 0
        party.save()
        messages.success(request, f'Party {party.name} updated!')
        return redirect('party_list')
    return render(request, 'masters/party_form.html', {'states': states, 'party': party})

@login_required
def party_delete(request, pk):
    party = get_object_or_404(Party, pk=pk)
    party.is_active = False
    party.save()
    messages.success(request, 'Party deleted!')
    return redirect('party_list')








