# inventory/views.py (Full Application Logic Component)
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum, F
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from reportlab.pdfgen import canvas
from .models import Product, Sale, SaleItem, Category
from .forms import ProductForm

# 1. DASHBOARD / INVENTORY LIST
# inventory/views.py ke andar inventory_list function ko isse replace karo:

@login_required
def inventory_list(request):
    """Main Inventory Dashboard displaying products, processing interactive real-time sidebar carts."""
    products = Product.objects.all()
    low_stock = Product.objects.filter(stock_quantity__lt=10)
    
    # 1. RETRIEVE ONGOING CART SESSIONS FOR SIDEBAR DRAWER LAYOUT
    cart = request.session.get('cart', [])
    cart_total = sum(float(item['total']) for item in cart)
    
    # Calculate Total Business Stats
    total_inventory_value = products.aggregate(
        total=Sum(F('stock_quantity') * F('buying_price'))
    )['total'] or 0
    
    total_sales_revenue = Sale.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Calculate Total Profit Dynamically
    total_profit = 0
    sales = Sale.objects.prefetch_related('items__product').all()
    for sale in sales:
        for item in sale.items.all():
            profit = (item.price_at_sale - item.product.buying_price) * item.quantity
            total_profit += profit

    # 2. INJECT 'cart' and 'cart_total' INSIDE CONTEXT LAYER
    context = {
        'products': products,
        'low_stock': low_stock,
        'total_value': total_inventory_value,
        'total_revenue': total_sales_revenue,
        'total_profit': total_profit,
        'total_items': products.count(),
        'cart': cart,              # Pass cart session list to template drawer
        'cart_total': cart_total,  # Pass sum total for pricing labels
    }
    return render(request, 'inventory/list_products.html', context)
# 2. DYNAMIC REGISTRATION SYSTEM
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome {user.username}.')
            return redirect('inventory_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# 3. SECURE CUSTOM LOGOUT BYPASS
def custom_logout(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')

# 4. FINANCIAL REPORT (Superuser Only)
@user_passes_test(lambda u: u.is_superuser)
def financial_report(request):
    products = Product.objects.all()
    total_value = products.aggregate(total=Sum(F('stock_quantity') * F('buying_price')))['total'] or 0
    total_revenue = Sale.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    total_profit = 0
    sales = Sale.objects.prefetch_related('items__product').all()
    for sale in sales:
        for item in sale.items.all():
            total_profit += (item.price_at_sale - item.product.buying_price) * item.quantity

    context = {
        'products': products,
        'total_revenue': total_revenue,
        'total_value': total_value,
        'total_profit': total_profit,
        'total_items': products.count(),
    }
    return render(request, 'inventory/financial_report.html', context)

# 5. UPGRADED ADD PRODUCT (With Media and Description Dynamic Overwrites)
@login_required
def add_product(request):
    products = Product.objects.all().order_by('name')

    if request.method == "POST":
        # FIXED: Added request.FILES to enable media stream streaming uploading
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            p_name = form.cleaned_data['name']
            
            product, created = Product.objects.get_or_create(name=p_name, defaults={
                'category': form.cleaned_data['category'],
                'buying_price': form.cleaned_data['buying_price'],
                'selling_price': form.cleaned_data['selling_price'],
                'stock_quantity': form.cleaned_data['stock_quantity'],
                'description': form.cleaned_data.get('description', ''),
                'image': form.cleaned_data.get('image', None),
            })
            
            if not created:
                product.category = form.cleaned_data['category']
                product.description = form.cleaned_data.get('description', product.description)
                
                # Check for dynamic image update overwrite
                if 'image' in request.FILES:
                    product.image = request.FILES['image']
                    
                if product.buying_price != form.cleaned_data['buying_price'] or \
                   product.selling_price != form.cleaned_data['selling_price']:
                    product.buying_price = form.cleaned_data['buying_price']
                    product.selling_price = form.cleaned_data['selling_price']
                    messages.warning(request, f"Prices updated for {p_name}!")
                
                product.stock_quantity += form.cleaned_data['stock_quantity']
                product.save()
                messages.success(request, f"Stock updated for {p_name}. New total: {product.stock_quantity}")
            else:
                messages.success(request, f"New product deployed to digital store shelf: {p_name}")

            return redirect('inventory_list')
    else:
        form = ProductForm()
        
    return render(request, 'inventory/add_product.html', {
        'form': form,
        'products': products
    })

# 6. DYNAMIC CREATION BILLING ENGINE WITH IN-CART OFFSET COUNTERS
@login_required
def create_bill(request):
    raw_products = Product.objects.all().order_by('name')
    cart = request.session.get('cart', [])
    
    products = []
    for prod in raw_products:
        cart_qty = 0
        for item in cart:
            if item['id'] == prod.id:
                cart_qty = item['qty']
                break
        
        products.append({
            'id': prod.id,
            'name': prod.name,
            'selling_price': prod.selling_price,
            'stock_quantity': prod.stock_quantity - cart_qty 
        })

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "add_to_cart":
            p_id = request.POST.get('product')
            qty = int(request.POST.get('quantity'))
            prod = Product.objects.get(id=p_id)
            
            existing_cart_qty = 0
            existing_item_index = -1
            
            for index, item in enumerate(cart):
                if item['id'] == prod.id:
                    existing_cart_qty = item['qty']
                    existing_item_index = index
                    break
            
            total_requested_qty = existing_cart_qty + qty
            
            if prod.stock_quantity >= total_requested_qty:
                if existing_item_index != -1:
                    cart[existing_item_index]['qty'] = total_requested_qty
                    cart[existing_item_index]['total'] = float(prod.selling_price * total_requested_qty)
                    messages.success(request, f"Updated '{prod.name}' quantity in cart to {total_requested_qty}.")
                else:
                    cart.append({
                        'id': prod.id, 
                        'name': prod.name, 
                        'qty': qty,
                        'price': float(prod.selling_price), 
                        'total': float(prod.selling_price * qty)
                    })
                    messages.success(request, f"'{prod.name}' added to cart.")
                
                request.session['cart'] = cart
            else:
                available_left = prod.stock_quantity - existing_cart_qty
                if existing_cart_qty > 0:
                    messages.error(request, f"⚠️ Stock Limit Error: You already have {existing_cart_qty} of '{prod.name}' in cart. Max remaining you can add is {available_left}!")
                else:
                    messages.error(request, f"⚠️ Stock Limit Error: Only {prod.stock_quantity} items of '{prod.name}' available. You requested {qty}!")
            
            return redirect('create_bill')

        elif action == "finalize_bill":
            customer = request.POST.get('customer')
            if not cart:
                messages.warning(request, "Your cart is empty!")
                return redirect('create_bill')
            
            try:
                with transaction.atomic():
                    new_sale = Sale.objects.create(customer_name=customer)
                    total = 0
                    for item in cart:
                        prod = Product.objects.get(id=item['id'])
                        SaleItem.objects.create(
                            sale=new_sale, 
                            product=prod, 
                            quantity=item['qty'], 
                            price_at_sale=item['price']
                        )
                        total += item['total']
                    new_sale.total_amount = total
                    new_sale.save()
                
                request.session['cart'] = []
                messages.success(request, f"Bill saved successfully for {customer}!")
                return redirect('sales_history')
                
            except ValidationError as e:
                messages.error(request, f"⚠️ Transaction Declined: {e.messages[0]}")
                return redirect('create_bill')

    return render(request, 'inventory/create_bill.html', {
        'products': products, 
        'cart': cart, 
        'cart_total': sum(i['total'] for i in cart)
    })

# 7. ADDITIONAL MANAGEMENT VIEWS
@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})

@login_required
def add_category(request):
    if request.method == "POST":
        name = request.POST.get('category_name')
        if name:
            Category.objects.get_or_create(name=name.strip())
            return redirect('add_product')
    return render(request, 'inventory/add_category.html')

@login_required
def sales_history(request):
    sales = Sale.objects.prefetch_related('items__product').all().order_by('-sale_date')
    return render(request, 'inventory/sales_history.html', {'sales': sales})

# 8. NATIVE COMPATIBLE DOWNLOAD MANAGER
@login_required
def download_bill(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bill_{sale.id}.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica", 12)
    p.drawString(50, 800, f"Bill ID: {sale.id}")
    p.drawString(50, 780, f"Customer: {sale.customer_name}")
    p.drawString(50, 760, f"Date: {sale.sale_date}")

    y = 720
    for item in sale.items.all():
        p.drawString(50, y, f"{item.product.name} - {item.quantity} x {item.price_at_sale}")
        y -= 20

    p.drawString(50, y - 20, f"Total Amount: {sale.total_amount}")
    p.save()
    return response

# 9. UTILITY SESSION VIEWS
@login_required
def unlock_session(request):
    if request.method == "POST":
        request.session['profit_unlocked'] = True
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'denied'}, status=403)

# 10. RECORD DELETION LOGIC (Superuser Guarded)
@login_required
def delete_product(request, pk):
    if not request.user.is_superuser:
        return redirect('inventory_list')
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('inventory_list')

@login_required
def delete_category(request, pk):
    if not request.user.is_superuser:
        return redirect('category_list')
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return redirect('category_list')

@login_required
def delete_sale(request, pk):
    if not request.user.is_superuser:
        return redirect('sales_history')
    sale = get_object_or_404(Sale, pk=pk)
    sale.delete()
    return redirect('sales_history')

# 11. CATEGORY FILTER VIEW
@login_required
def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category).order_by('name')
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'inventory/category_products.html', context)

# 12. NEW CUSTOMER-FACING INTERACTIVE STOREFRONT VIEW
@login_required
def storefront_view(request):
    """Blinkit Grid display filtering active product media items."""
    products = Product.objects.filter(is_active=True).order_by('name')
    return render(request, 'inventory/storefront.html', {'products': products})



    # inventory/views.py ke bilkul bottom par paste karo:
# inventory/views.py ke andar add_to_cart_fast ko replace karo aur remove_from_cart ko uske neeche jod do:

@login_required
def add_to_cart_fast(request, product_id):
    """Dynamic bulk and retail quantity collector updating active session dictionary vectors."""
    prod = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', [])
    
    # Custom post data validation layer (Agar direct input se dynamic quantity aati h to use pakdo)
    qty_to_add = int(request.POST.get('bulk_qty', 1))
    if qty_to_add < 1:
        qty_to_add = 1
        
    existing_cart_qty = 0
    existing_item_index = -1
    
    for index, item in enumerate(cart):
        if item['id'] == prod.id:
            existing_cart_qty = item['qty']
            existing_item_index = index
            break
            
    total_requested_qty = existing_cart_qty + qty_to_add
    
    if prod.stock_quantity >= total_requested_qty:
        if existing_item_index != -1:
            cart[existing_item_index]['qty'] = total_requested_qty
            cart[existing_item_index]['total'] = float(prod.selling_price * total_requested_qty)
        else:
            cart.append({
                'id': prod.id,
                'name': prod.name,
                'qty': qty_to_add,
                'price': float(prod.selling_price),
                'total': float(prod.selling_price * qty_to_add)
            })
        request.session['cart'] = cart
        messages.success(request, f"⚡ '{prod.name}' ({qty_to_add} Units) added directly into your billing layer!")
    else:
        available_left = prod.stock_quantity - existing_cart_qty
        if existing_cart_qty > 0:
            messages.error(request, f"⚠️ Stock Exhausted: You already have {existing_cart_qty} in cart. Max remaining you can add is {available_left}!")
        else:
            messages.error(request, f"⚠️ Stock Exhausted: Only {prod.stock_quantity} available. You requested {qty_to_add}!")
            
    # Redirect smoothly back to inventory interface panel
    return redirect('inventory_list')

@login_required
def remove_from_cart(request, product_id):
    """Wipes out targeted item instances inside ongoing checkout session maps."""
    cart = request.session.get('cart', [])
    
    # Re-filtering list excluding current matched item array parameters
    updated_cart = [item for item in cart if item['id'] != product_id]
    
    request.session['cart'] = updated_cart
    messages.warning(request, "🗑️ Item removed successfully from active billing bucket.")
    return redirect('inventory_list')