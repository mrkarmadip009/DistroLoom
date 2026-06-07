# inventory/urls.py
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
    path('category/<int:category_id>/products/', views.category_products, name='category_products'),
    
    # DYNAMIC Q-COMMERCE FAST MODIFIERS & DRAWER LAYER ENDPOINTS
    path('store/', views.storefront_view, name='storefront_view'),
    path('store/add-fast/<int:product_id>/', views.add_to_cart_fast, name='add_to_cart_fast'),
    path('store/remove-item/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Authentication Framework Management Layer
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    
    # Actions Layer Routing Paths
    path('product/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('category/delete/<int:pk>/', views.delete_category, name='delete_category'),
    path('sale/delete/<int:pk>/', views.delete_sale, name='delete_sale'),
    path('download-bill/<int:sale_id>/', views.download_bill, name='download_bill'),
]