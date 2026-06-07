# inventory/forms.py
from django import forms
from .models import Product, Category

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # Hamne fields list me 'description', 'image' aur 'is_active' ko jod diya hai
        fields = ['name', 'category', 'description', 'image', 'stock_quantity', 'buying_price', 'selling_price', 'is_active']