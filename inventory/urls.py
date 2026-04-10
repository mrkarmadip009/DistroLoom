from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('dashboard/', views.inventory_list, name='inventory_list'),
    path('categories/', views.category_list, name='category_list'),
    path('category/add/', views.add_category, name='add_category'),
    path('add/', views.add_product, name='add_product'),
    path('bill/', views.create_bill, name='create_bill'),
    path('sales/', views.sales_history, name='sales_history'),
    path('reports/finance/', views.financial_report, name='financial_report'),
    path('unlock-profit/', views.unlock_session, name='unlock_session'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
]