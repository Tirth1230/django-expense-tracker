from django import forms
from .models import Expense, Category

class ExpenseForm(forms.ModelForm):
    """
    Form for creating and updating Expense objects.
    """
    # Use a DateInput widget to get a nice calendar picker for the date
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'})
    )

    class Meta:
        model = Expense
        fields = ['amount', 'description', 'category', 'date']

    def __init__(self, *args, **kwargs):
        # Pop the user out of kwargs before calling super
        user = kwargs.pop('user', None)
        super(ExpenseForm, self).__init__(*args, **kwargs)
        
        # This is the corrected line:
        # Instead of user.categories, we directly query the Category model
        # to find all categories belonging to the current user.
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
        
        # Add Tailwind classes to the other form fields for consistent styling
        self.fields['amount'].widget.attrs.update({'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm', 'placeholder': 'e.g., 50.00'})
        self.fields['description'].widget.attrs.update({'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm', 'placeholder': 'e.g., Lunch with client'})
        self.fields['category'].widget.attrs.update({'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'})

