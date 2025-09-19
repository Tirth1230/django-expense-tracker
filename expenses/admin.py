from django.contrib import admin
from .models import Category, Expense

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=('name','user')
    list_filter=('user',)
    search_fields=('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('amount','category','user','date')
    list_filter = ('user','category','date')
    search_fields = ("description", 'category__name')
    date_hierarchy = 'date'