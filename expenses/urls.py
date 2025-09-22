from django.urls import path
from . import views

urlpatterns = [
    path('register/',views.register_view, name='register'),
    path('login/', views.login_view,name='login'),
    path('logout/',views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
]
