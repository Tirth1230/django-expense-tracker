from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Core App
    path('', views.dashboard, name='dashboard'),
    path('edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    
    # Reporting & Exporting
    path('report/', views.report_view, name='report'),
    path('export-csv/', views.export_csv, name='export_csv'),
    
    # Google Drive Integration
    path('upload-to-drive/', views.upload_to_drive, name='upload_to_drive'),
    path('oauth2callback', views.oauth2callback, name='oauth2callback'),

    path('email-report/', views.email_report, name='email_report'),
]


