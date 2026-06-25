from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ServiceCall
from masters.models import Customer
import datetime

def generate_call_number():
    last = ServiceCall.objects.order_by('-id').first()
    num = int(last.call_number.replace('SRV', '')) + 1 if last else 1
    return f"SRV{num:04d}"

@login_required
def call_list(request):
    status_filter = request.GET.get('status', '')
    calls = ServiceCall.objects.select_related('customer').all()
    if status_filter:
        calls = calls.filter(status=status_filter)
    return render(request, 'service_call/call_list.html', {
        'calls': calls,
        'status_filter': status_filter
    })

@login_required
def call_add(request):
    customers = Customer.objects.filter(is_active=True)
    if request.method == 'POST':
        ServiceCall.objects.create(
            call_number=generate_call_number(),
            customer_id=request.POST['customer'],
            contact_person=request.POST.get('contact_person', ''),
            contact_phone=request.POST.get('contact_phone', ''),
            call_date=request.POST['call_date'],
            issue_type=request.POST['issue_type'],
            description=request.POST['description'],
            priority=request.POST.get('priority', 'medium'),
            assigned_to=request.POST.get('assigned_to', ''),
            charges=request.POST.get('charges', 0),
        )
        messages.success(request, 'Service call registered!')
        return redirect('call_list')
    return render(request, 'service_call/call_form.html', {
        'customers': customers,
        'today': datetime.date.today(),
        'call_number': generate_call_number(),
        'title': 'New Service Call'
    })

@login_required
def call_edit(request, pk):
    call = get_object_or_404(ServiceCall, pk=pk)
    customers = Customer.objects.filter(is_active=True)
    if request.method == 'POST':
        call.customer_id = request.POST['customer']
        call.contact_person = request.POST.get('contact_person', '')
        call.contact_phone = request.POST.get('contact_phone', '')
        call.call_date = request.POST['call_date']
        call.issue_type = request.POST['issue_type']
        call.description = request.POST['description']
        call.priority = request.POST.get('priority', 'medium')
        call.status = request.POST.get('status', 'open')
        call.assigned_to = request.POST.get('assigned_to', '')
        call.resolution = request.POST.get('resolution', '')
        call.charges = request.POST.get('charges', 0)
        if call.status == 'resolved':
            call.resolved_date = datetime.date.today()
        call.save()
        messages.success(request, 'Service call updated!')
        return redirect('call_list')
    return render(request, 'service_call/call_form.html', {
        'customers': customers,
        'obj': call,
        'title': 'Edit Service Call'
    })

@login_required
def call_detail(request, pk):
    call = get_object_or_404(ServiceCall, pk=pk)
    return render(request, 'service_call/call_detail.html', {'call': call})

@login_required
def call_delete(request, pk):
    call = get_object_or_404(ServiceCall, pk=pk)
    call.delete()
    messages.success(request, 'Service call deleted!')
    return redirect('call_list')
