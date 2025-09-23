import json
from datetime import datetime, timedelta
from django.urls import reverse # <-- FIX: Added the missing import
from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Expense, Category
from .forms import ExpenseForm, CustomUserCreationForm
from django.http import HttpResponse
import csv
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags

# Imports for Google Drive API
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io


def register_view(request):
    """Handles user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create some default categories for the new user
            Category.objects.create(user=user, name='Food')
            Category.objects.create(user=user, name='Transport')
            Category.objects.create(user=user, name='Bills')
            Category.objects.create(user=user, name='Entertainment')
            Category.objects.create(user=user, name='Other')

            login(request, user)
            messages.success(request, 'Registration successful. You are now logged in.')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'expenses/register.html', {'form': form})


def login_view(request):
    """Handles user login."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'expenses/login.html', {'form': form})


def logout_view(request):
    """Handles user logout."""
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')


@login_required
def dashboard(request):
    """
    Displays the user's expenses and a form to add a new expense.
    """
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm(user=request.user)

    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    
    context = {
        'form': form,
        'expenses': expenses,
    }
    return render(request, 'expenses/dashboard.html', context)

@login_required
def edit_expense(request, expense_id):
    """Handles editing an existing expense."""
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm(instance=expense, user=request.user)
    
    return render(request, 'expenses/edit_expense.html', {'form': form, 'expense': expense})


@login_required
def delete_expense(request, expense_id):
    """Handles deleting an existing expense."""
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('dashboard')
    return redirect('dashboard')


@login_required
def report_view(request):
    """
    Displays a report of expenses, filterable by month and year.
    """
    today = timezone.now().date()
    
    try:
        selected_year = int(request.GET.get('year', today.year))
        selected_month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        selected_year = today.year
        selected_month = today.month

    expenses_for_period = Expense.objects.filter(
        user=request.user,
        date__year=selected_year,
        date__month=selected_month
    )

    total_expenses = expenses_for_period.aggregate(Sum('amount'))['amount__sum'] or 0
    category_summary = expenses_for_period.values('category__name').annotate(total=Sum('amount')).order_by('-total')

    chart_labels = [item['category__name'] for item in category_summary]
    chart_data = [float(item['total']) for item in category_summary]

    expense_dates = Expense.objects.filter(user=request.user).dates('date', 'year', order='DESC')
    available_years = [d.year for d in expense_dates]
    if not available_years or today.year not in available_years:
        available_years.insert(0, today.year)
    
    month_name = datetime(selected_year, selected_month, 1).strftime('%B')
    
    # <-- FIX: Reverted to the simple, working format for months
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    context = {
        'total_expenses': total_expenses,
        'category_summary': category_summary,
        'current_month': f"{month_name} {selected_year}",
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'available_years': available_years,
        'months': months,
        'selected_year': selected_year,
        'selected_month': selected_month,
    }
    return render(request, 'expenses/report.html', context)


@login_required
def email_report(request):
    """Prepares and sends the expense report via email."""
    user = request.user
    if not user.email:
        messages.error(request, "Your profile doesn't have an email address configured.")
        return redirect('report')

    today = timezone.now().date()
    
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        year = today.year
        month = today.month

    expenses = Expense.objects.filter(user=user, date__year=year, date__month=month)
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    category_summary = expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')
    
    month_name = datetime(year, month, 1).strftime('%B %Y')

    email_context = {
        'user': user,
        'category_summary': category_summary,
        'total_expenses': total_expenses,
        'report_month': month_name,
    }
    
    html_message = render_to_string('expenses/email/report_email.html', email_context)
    plain_message = strip_tags(html_message)
    subject = f'Your Expense Report for {month_name}'
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        messages.success(request, f"Your expense report for {month_name} has been sent to {user.email}.")
    except Exception as e:
        messages.error(request, f"An error occurred while sending the email: {e}")

    return redirect(f"{reverse('report')}?year={year}&month={month}")


@login_required
def export_csv(request):
    today = timezone.now().date()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        year = today.year
        month = today.month
    
    expenses = Expense.objects.filter(user=request.user, date__year=year, date__month=month)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="expense_report_{year}-{month:02d}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Description', 'Category', 'Amount'])
    for expense in expenses:
        writer.writerow([expense.date, expense.description, expense.category.name, expense.amount])
    return response


# --- Google Drive Integration ---
SCOPES = ['https://www.googleapis.com/auth/drive.file']
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

@login_required
def upload_to_drive(request):
    creds = None
    # ... (rest of the Google Drive code is unchanged)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        else:
            return redirect('authorize_drive')

    try:
        service = build('drive', 'v3', credentials=creds)
        
        today = timezone.now().date()
        try:
            year = int(request.GET.get('year', today.year))
            month = int(request.GET.get('month', today.month))
        except(ValueError, TypeError):
            year = today.year
            month = today.month
            
        expenses = Expense.objects.filter(user=request.user, date__year=year, date__month=month)

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['Date', 'Description', 'Category', 'Amount'])
        for expense in expenses:
            writer.writerow([expense.date, expense.description, expense.category.name, expense.amount])
        
        csv_buffer.seek(0)

        file_name = f'expense_report_{year}-{month:02d}.csv'
        file_metadata = {'name': file_name}
        media = MediaIoBaseUpload(io.BytesIO(csv_buffer.getvalue().encode()), mimetype='text/csv')

        file = service.files().create(body=file_metadata, media_body=media, fields='id,name').execute()
        
        messages.success(request, f"Successfully uploaded '{file.get('name')}' to your Google Drive.")

    except Exception as e:
        messages.error(request, f"An error occurred: {e}")

    return redirect(f"{reverse('report')}?year={year}&month={month}")


@login_required
def authorize_drive(request):
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', SCOPES,
        redirect_uri=request.build_absolute_uri(reverse('oauth2callback'))
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    request.session['google_oauth_state'] = state
    return redirect(authorization_url)


@login_required
def oauth2callback(request):
    state = request.session['google_oauth_state']
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', SCOPES, state=state,
        redirect_uri=request.build_absolute_uri(reverse('oauth2callback'))
    )
    
    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    with open('token.json', 'w') as token:
        token.write(credentials.to_json())

    # After getting token, we need to pass the original filters back to the upload function
    # For now, we'll just redirect to the general upload, which will use the current month/year
    return redirect('upload_to_drive')

