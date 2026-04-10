# DistroLoom/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views # Import this here!

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. This redirects the very first visit to the login page
    path('', RedirectView.as_view(url='/login/'), name='root_redirect'),
    
    # 2. Add these AUTH paths here so http://127.0.0.1:8000/login/ works!
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # 3. Your app URLs
    path('inventory/', include('inventory.urls')),
]