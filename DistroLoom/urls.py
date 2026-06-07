# DistroLoom/urls.py (Main Project Router)
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Panel Route
    path('admin/', admin.site.urls),
    
    # 1. Absolute Base Redirect to Login System smoothly
    path('', RedirectView.as_view(url='/inventory/login/'), name='root_redirect'),
    
    # 2. Main Core Application Link
    path('inventory/', include('inventory.urls')),
]

# 3. MAGIC COUPLING LAYER: Uploaded Photos (Swiggy UI Assets) ko browser me server karne ke liye
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)