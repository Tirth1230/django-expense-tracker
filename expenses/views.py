from django.shortcuts import render,redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages

# Create your views here.

def register_view(request):

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "registration successful")
            return redirect('login')
        else:
            messages.error(request, 'Unsuccessful registration. Invalid information.')

    else:
        form = UserCreationForm()
    return render(request, 'expenses/register.html',{'form' : form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username,password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}")
                return redirect(login)
            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request,"Invalod username or password")
    form = AuthenticationForm()
    return render(request,'expenses/login.html', {'form' : form})

def logout_view(request):
    logout(request)
    messages.info(request,"you have successfully logged out.")
    return redirect('login')