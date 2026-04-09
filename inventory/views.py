from django.shortcuts import render, redirect
from .forms import ProductForm
from .models import Product, Sale  # Make sure Sale is here

def inventory_list(request):
    products = Product.objects.all()
    low_stock = Product.objects.filter(stock_quantity__lt=10)
    return render(request, 'inventory/list_products.html', {
        'products': products, 
        'low_stock': low_stock
    })

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})

def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory_list')
    else:
        form = ProductForm()
    return render(request, 'inventory/add_product.html', {'form': form})

from .models import Category # Ensure Category is imported at the top

def add_category(request):
    if request.method == "POST":
        name = request.POST.get('category_name')
        if name:
            Category.objects.create(name=name)
            return redirect('add_product') # Goes back to the product form
    return render(request, 'inventory/add_category.html')

def sales_history(request):
    # This pulls every bill ever made, newest first
    sales = Sale.objects.all().order_by('-sale_date')
    return render(request, 'inventory/sales_history.html', {'sales': sales})
# This is the function your error is complaining about:
def create_bill(request):
    products = Product.objects.all()
    # Get current cart from session or create empty list
    cart = request.session.get('cart', [])

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "add_to_cart":
            p_id = request.POST.get('product')
            qty = int(request.POST.get('quantity'))
            product = Product.objects.get(id=p_id)
            
            cart.append({
                'id': product.id,
                'name': product.name,
                'qty': qty,
                'price': float(product.selling_price),
                'total': float(product.selling_price * qty)
            })
            request.session['cart'] = cart
            return redirect('create_bill')

        elif action == "finalize_bill":
            cust = request.POST.get('customer')
            new_sale = Sale.objects.create(customer_name=cust)
            grand_total = 0
            
            for item in cart:
                prod = Product.objects.get(id=item['id'])
                SaleItem.objects.create(
                    sale=new_sale,
                    product=prod,
                    quantity=item['qty'],
                    price_at_sale=item['price']
                )
                grand_total += item['total']
            
            new_sale.total_amount = grand_total
            new_sale.save()
            
            # Clear cart
            request.session['cart'] = []
            return render(request, 'inventory/bill_success.html', {'sale': new_sale})

        elif action == "clear":
            request.session['cart'] = []
            return redirect('create_bill')

    return render(request, 'inventory/create_bill.html', {
        'products': products,
        'cart': cart,
        'cart_total': sum(item['total'] for item in cart)
    })