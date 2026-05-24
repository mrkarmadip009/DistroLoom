# DistroLoom/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from inventory import views as inventory_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Redirects the base URL (http://127.0.0.1:8000/) directly to your login system
    path('', RedirectView.as_view(url='inventory/login/'), name='root_redirect'),
    
    # 2. App URLs (This routes everything neatly through your inventory app)
    path('inventory/', include('inventory.urls')),
    
    # 3. Dedicated registration path linking directly to your view
    path('register/', inventory_views.register, name='register'),
]