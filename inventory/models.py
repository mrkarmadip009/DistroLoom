# inventory/models.py
from django.db import models
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    stock_quantity = models.PositiveIntegerField(default=0)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    added_on = models.DateTimeField(auto_now_add=True)
    
    # NEW SWIGGY / BLINKIT Q-COMMERCE ASSETS
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True) # Instamart pe listing hide/show karne ke liye

    @property
    def profit_per_item(self):
        return self.selling_price - self.buying_price

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} in stock)"

# inventory/models.py ke andar sirf Sale model ko isse replace karo:
from django.contrib.auth.models import User

# inventory/models.py ke andar Sale model ko isse replace karo:
from django.contrib.auth.models import User

class Sale(models.Model):
    customer_name = models.CharField(max_length=200)
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # NEW FLAG: True tab hoga jab normal user ise apni screen se delete marega
    deleted_by_user = models.BooleanField(default=False)

    def __str__(self):
        return f"Bill for {self.customer_name} - {self.sale_date.date()}"

# inventory/models.py ke andar SaleItem model ko isse completely replace karo:

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} inside Bill #{self.sale.id}"

    def save(self, *args, **kwargs):
        """
        FIXED: Removed the duplicate stock_quantity check from here!
        We handle all limits in views.py, so this model just saves records cleanly.
        """
        super().save(*args, **kwargs)