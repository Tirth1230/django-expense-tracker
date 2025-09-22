from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Expense, Category
from .forms import ExpenseForm

def register_view(request):
    """Handles user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful. You are now logged in.')
            return redirect('dashboard')
        else:
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

    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    
    # Create some default categories if the user has none
    if not Category.objects.filter(user=request.user).exists():
        Category.objects.create(user=request.user, name='Food')
        Category.objects.create(user=request.user, name='Transport')
        Category.objects.create(user=request.user, name='Bills')
        Category.objects.create(user=request.user, name='Entertainment')

    context = {
        'form': form,
        'expenses': expenses,
    }
    return render(request, 'expenses/dashboard.html', context)

