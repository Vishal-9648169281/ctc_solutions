from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from .models import Project, ProjectPayment
from masters.models import Customer
import datetime

@login_required
def project_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment_status', '')

    projects = Project.objects.filter(is_active=True).select_related('client')

    if query:
        projects = projects.filter(
            Q(project_name__icontains=query) |
            Q(client__name__icontains=query) |
            Q(client_name_manual__icontains=query) |
            Q(technology__icontains=query)
        )
    if status_filter:
        projects = projects.filter(status__iexact=status_filter)
    if payment_filter:
        projects = projects.filter(payment_status__iexact=payment_filter)

    total_projects = Project.objects.filter(is_active=True).count()
    live_count = Project.objects.filter(is_active=True, status__iexact='Live').count()
    overdue_count = Project.objects.filter(is_active=True, payment_status__iexact='Overdue').count()
    total_amc_value = Project.objects.filter(is_active=True, payment_type='amc').aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'projects/project_list.html', {
        'projects': projects,
        'query': query,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'total_projects': total_projects,
        'live_count': live_count,
        'overdue_count': overdue_count,
        'total_amc_value': total_amc_value,
    })

@login_required
def project_add(request):
    customers = Customer.objects.filter(is_active=True)
    if request.method == 'POST':
        project = Project.objects.create(
            project_name=request.POST['project_name'],
            client_id=request.POST.get('client') or None,
            client_name_manual=request.POST.get('client_name_manual', ''),
            technology=request.POST.get('technology', ''),
            description=request.POST.get('description', ''),
            status=request.POST.get('status', 'Live'),
            server_details=request.POST.get('server_details', ''),
            login_url=request.POST.get('login_url', ''),
            login_username=request.POST.get('login_username', ''),
            login_password=request.POST.get('login_password', ''),
            payment_type=request.POST.get('payment_type', 'onetime'),
            amount=request.POST.get('amount') or 0,
            amc_start_date=request.POST.get('amc_start_date') or None,
            amc_end_date=request.POST.get('amc_end_date') or None,
            subscription_due_day=request.POST.get('subscription_due_day') or None,
            last_payment_date=request.POST.get('last_payment_date') or None,
            next_due_date=request.POST.get('next_due_date') or None,
            payment_status=request.POST.get('payment_status', 'Pending'),
            start_date=request.POST.get('start_date') or None,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, f'Project "{project.project_name}" added successfully!')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'projects/project_form.html', {
        'title': 'Add New Project',
        'customers': customers,
    })

@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    customers = Customer.objects.filter(is_active=True)
    if request.method == 'POST':
        project.project_name = request.POST['project_name']
        project.client_id = request.POST.get('client') or None
        project.client_name_manual = request.POST.get('client_name_manual', '')
        project.technology = request.POST.get('technology', '')
        project.description = request.POST.get('description', '')
        project.status = request.POST.get('status', 'Live')
        project.server_details = request.POST.get('server_details', '')
        project.login_url = request.POST.get('login_url', '')
        project.login_username = request.POST.get('login_username', '')
        project.login_password = request.POST.get('login_password', '')
        project.payment_type = request.POST.get('payment_type', 'onetime')
        project.amount = request.POST.get('amount') or 0
        project.amc_start_date = request.POST.get('amc_start_date') or None
        project.amc_end_date = request.POST.get('amc_end_date') or None
        project.subscription_due_day = request.POST.get('subscription_due_day') or None
        project.last_payment_date = request.POST.get('last_payment_date') or None
        project.next_due_date = request.POST.get('next_due_date') or None
        project.payment_status = request.POST.get('payment_status', 'Pending')
        project.start_date = request.POST.get('start_date') or None
        project.notes = request.POST.get('notes', '')
        project.save()
        messages.success(request, 'Project updated successfully!')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'projects/project_form.html', {
        'title': 'Edit Project',
        'obj': project,
        'customers': customers,
    })

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    payments = project.payments.all()
    total_received = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    return render(request, 'projects/project_detail.html', {
        'project': project,
        'payments': payments,
        'total_received': total_received,
    })

@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.is_active = False
    project.save()
    messages.success(request, 'Project removed!')
    return redirect('project_list')

@login_required
def payment_add(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        ProjectPayment.objects.create(
            project=project,
            amount=request.POST['amount'],
            payment_date=request.POST['payment_date'],
            payment_mode=request.POST.get('payment_mode', ''),
            period_covered=request.POST.get('period_covered', ''),
            notes=request.POST.get('notes', ''),
        )
        project.last_payment_date = request.POST['payment_date']
        project.payment_status = 'Paid'
        if request.POST.get('next_due_date'):
            project.next_due_date = request.POST.get('next_due_date')
        project.save()
        messages.success(request, 'Payment recorded successfully!')
        return redirect('project_detail', pk=pk)
    return redirect('project_detail', pk=pk)

@login_required
def payment_delete(request, pk, payment_pk):
    payment = get_object_or_404(ProjectPayment, pk=payment_pk, project_id=pk)
    payment.delete()
    messages.success(request, 'Payment record deleted!')
    return redirect('project_detail', pk=pk)
