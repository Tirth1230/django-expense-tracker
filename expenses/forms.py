from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Expense, Category

class CustomUserCreationForm(UserCreationForm):
    """
    A custom user creation form that includes a required email field.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm', 'placeholder': 'you@example.com'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)


class ExpenseForm(forms.ModelForm):
    """
    A form for creating and updating Expense objects, customized for the user.
    """
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ExpenseForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)

    class Meta:
        model = Expense
        fields = ['amount', 'description', 'category', 'date']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm', 'placeholder': 'e.g., 50.00'}),
            'description': forms.Textarea(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm', 'rows': 3, 'placeholder': 'e.g., Lunch with client'}),
            'category': forms.Select(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'date': forms.DateInput(attrs={'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm', 'type': 'date'}),
        }

