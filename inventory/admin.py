from django.contrib import admin
from .models import Category, Product, Sale, SaleItem

# This allows you to see SaleItems inside the Sale page
class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price_at_sale']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'sale_date', 'total_amount']
    inlines = [SaleItemInline] # Shows the items bought on the same page!

admin.site.register(Category)
admin.site.register(Product)