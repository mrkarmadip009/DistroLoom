from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('categories/', views.category_list, name='category_list'),
    path('category/add/', views.add_category, name='add_category'),
    path('add/', views.add_product, name='add_product'),
    path('bill/', views.create_bill, name='create_bill'),
    path('sales/', views.sales_history, name='sales_history'),
]