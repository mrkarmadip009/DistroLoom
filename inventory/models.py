from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    # Link to the Category model instead of using a choice list
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    stock_quantity = models.PositiveIntegerField(default=0)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    added_on = models.DateTimeField(auto_now_add=True)

    @property
    def profit_per_item(self):
        return self.selling_price - self.buying_price

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} in stock)"

class Sale(models.Model):
    customer_name = models.CharField(max_length=200)
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Bill for {self.customer_name} - {self.sale_date.date()}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2) # Price can change over time

    def save(self, *args, **kwargs):
        # Reduce stock when item is added to bill
        self.product.stock_quantity -= self.quantity
        self.product.save()
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Calculate total and reduce stock automatically
        self.total_bill = self.product.selling_price * self.quantity_sold
        self.product.stock_quantity -= self.quantity_sold
        self.product.save()
        super().save(*args, **kwargs)