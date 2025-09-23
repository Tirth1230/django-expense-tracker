from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Expense, Category
from .forms import ExpenseForm
from datetime import datetime
from django.db.models import Sum
import json 
import csv
from django.http import HttpResponse

def register_view(request):
    """Handles user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create default categories for the new user, this is the correct place for it
            Category.objects.create(user=user, name='Food')
            Category.objects.create(user=user, name='Transport')
            Category.objects.create(user=user, name='Bills')
            Category.objects.create(user=user, name='Entertainment')
            login(request, user)
            messages.success(request, 'Registration successful. You are now logged in.')
            return redirect('dashboard')
        else:
            # Add form errors to messages for better feedback
            for field in form:
                for error in field.errors:
                    messages.error(request, f"{field.label}: {error}")
            messages.error(request, 'Unsuccessful registration. Invalid information.')
    else:
        form = UserCreationForm()
    return render(request, 'expenses/register.html', {'form': form})


def login_view(request):
    """Handles user login."""
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
            messages.error(request, 'Invalid username or password.')
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

    expenses = Expense.objects.filter(user=request.user)
    
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
            # CRITICAL FIX: Always redirect after a successful POST.
            # This prevents the duplicate entry bug.
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
        # CRITICAL FIX: Always redirect after a successful POST.
        # This makes the delete action clean and reliable.
        return redirect('dashboard')
    
    # This view only handles POST, so a GET request will just go back to the dashboard.
    return redirect('dashboard')

@login_required
def report_view(request):
    """
    Generates a report of expenses for the current month, grouped by category.
    """
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Get all expenses for the current user and current month
    expenses = Expense.objects.filter(
        user=request.user, 
        date__year=current_year, 
        date__month=current_month
    )

    # Calculate the total expenses for the month
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0

    # Group expenses by category and calculate the sum for each
    category_summary = (
        expenses.values('category__name')
        .annotate(total_amount=Sum('amount'))
        .order_by('-total_amount')
    )

    chart_labels = [item['category__name'] for item in category_summary]
    chart_data = [float(item['total_amount']) for item in category_summary]

    context = {
        'total_expenses': total_expenses,
        'category_summary': category_summary,
        'report_month': datetime.now().strftime('%B %Y'),
        # Pass the chart data to the template, safely encoded as JSON
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'expenses/report.html', context)


@login_required
def export_csv(request):
    """
    Handles the logic for exporting the current month's expenses to a CSV file.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expense_report_{}.csv"'.format(datetime.now().strftime("%Y_%m"))

    writer = csv.writer(response)
    writer.writerow(['Date', 'Description', 'Category', 'Amount'])

    current_month = datetime.now().month
    current_year = datetime.now().year

    expenses = Expense.objects.filter(
        user=request.user,
        date__year=current_year,
        date__month=current_month
    ).order_by('date')

    for expense in expenses:
        writer.writerow([expense.date, expense.description, expense.category.name, expense.amount])

    return response
