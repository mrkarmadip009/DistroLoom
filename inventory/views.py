from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib import messages
from .models import Product, Sale, SaleItem, Category
from .forms import ProductForm

def inventory_list(request):
    products = Product.objects.all()
    low_stock = Product.objects.filter(stock_quantity__lt=10)
    return render(request, 'inventory/list_products.html', {'products': products, 'low_stock': low_stock})

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})

def add_category(request):
    if request.method == "POST":
        name = request.POST.get('category_name')
        if name:
            Category.objects.create(name=name)
            return redirect('add_product')
    return render(request, 'inventory/add_category.html')
# inventory/views.py

from .forms import ProductForm
from .models import Product, Category

def add_product(request):
    products = Product.objects.all().order_by('name')

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            p_name = form.cleaned_data['name']
            
            # Smart logic: Update if name exists, create if it doesn't
            product, created = Product.objects.get_or_create(name=p_name, defaults={
                'category': form.cleaned_data['category'],
                'buying_price': form.cleaned_data['buying_price'],
                'selling_price': form.cleaned_data['selling_price'],
                'stock_quantity': form.cleaned_data['stock_quantity'],
            })
            
            if not created:
                # If product already exists, we UPDATE the fields
                product.category = form.cleaned_data['category']
                
                # Check if price changed
                if product.buying_price != form.cleaned_data['buying_price'] or \
                   product.selling_price != form.cleaned_data['selling_price']:
                    product.buying_price = form.cleaned_data['buying_price']
                    product.selling_price = form.cleaned_data['selling_price']
                    messages.warning(request, f"Prices updated for {p_name}!")
                
                # Add new quantity to existing stock
                product.stock_quantity += form.cleaned_data['stock_quantity']
                product.save()
                messages.success(request, f"Stock updated for {p_name}. New total: {product.stock_quantity}")
            else:
                messages.success(request, f"New product created: {p_name}")

            return redirect('inventory_list')
    else:
        form = ProductForm()
        
    return render(request, 'inventory/add_product.html', {
        'form': form,
        'products': products # We pass the list of products for the selector
    })

def create_bill(request):
    products = Product.objects.all()
    cart = request.session.get('cart', [])

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "add_to_cart":
            p_id = request.POST.get('product')
            qty = int(request.POST.get('quantity'))
            prod = Product.objects.get(id=p_id)
            
            if prod.stock_quantity >= qty:
                cart.append({
                    'id': prod.id, 'name': prod.name, 'qty': qty,
                    'price': float(prod.selling_price), 'total': float(prod.selling_price * qty)
                })
                request.session['cart'] = cart
            else:
                messages.error(request, f"Insufficient stock for {prod.name}")
            return redirect('create_bill')

        elif action == "finalize_bill":
            customer = request.POST.get('customer')
            if not cart:
                return redirect('create_bill')
            
            with transaction.atomic():
                new_sale = Sale.objects.create(customer_name=customer)
                total = 0
                for item in cart:
                    prod = Product.objects.get(id=item['id'])
                    # Reduction of stock logic happens in SaleItem.save()
                    SaleItem.objects.create(
                        sale=new_sale, product=prod, 
                        quantity=item['qty'], price_at_sale=item['price']
                    )
                    total += item['total']
                new_sale.total_amount = total
                new_sale.save()
            
            request.session['cart'] = []
            return redirect('sales_history')

    return render(request, 'inventory/create_bill.html', {
        'products': products, 'cart': cart, 'cart_total': sum(i['total'] for i in cart)
    })

def sales_history(request):
    sales = Sale.objects.prefetch_related('items__product').all().order_by('-sale_date')
    return render(request, 'inventory/sales_history.html', {'sales': sales})