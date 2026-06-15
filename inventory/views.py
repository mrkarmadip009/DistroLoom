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

# inventory/views.py ke andar inventory_list function ko isse replace karo:

@login_required
def inventory_list(request):
    """Main Inventory Dashboard displaying products with unified list/dict cart compatibility."""
    products = Product.objects.all()
    low_stock = Product.objects.filter(stock_quantity__lt=10)
    
    # 1. RETRIEVE ONGOING CART SESSIONS SAFE LAYER
    cart_session = request.session.get('cart', {})
    
    # FIXED: Normalize data to always fallback as an iterable list structure cleanly
    cart_list = []
    if isinstance(cart_session, dict):
        cart_list = list(cart_session.values())
    elif isinstance(cart_session, list):
        cart_list = cart_session

    # 2. FIXED CRASHING GENEXPR: Loop through the normalized cart list safely
    cart_total = sum(float(item['total']) for item in cart_list if isinstance(item, dict) and 'total' in item)
    
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

    # Inject variables inside the context layout layer
    context = {
        'products': products,
        'low_stock': low_stock,
        'total_value': total_inventory_value,
        'total_revenue': total_sales_revenue,
        'total_profit': total_profit,
        'total_items': products.count(),
        'cart': cart_list,          # Pass standardized list format to sidebar templates
        'cart_total': cart_total,   # Pass safe accumulated price labels
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
    # BACKEND GUARD: Agar user admin nahi hai, toh use chupchaap dashboard par bhej do!
    if not request.user.is_superuser:
        messages.error(request, "⚠️ Access Denied: Only admins can manage stock configurations!")
        return redirect('inventory_list')
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
# inventory/views.py ke andar purana create_bill isse badlo:
# inventory/views.py ke andar create_bill function ko isse replace karo:

@login_required
def create_bill(request):
    """
    Handles synchronized fallback billing architecture supporting both dictionary
    and list session cart structures cleanly without double-deducting database stock.
    """
    raw_products = Product.objects.all().order_by('name')
    cart_session = request.session.get('cart', {})
    
    # Normalize cart data to handle both list and dictionary fallback storage seamlessly
    cart_list = []
    if isinstance(cart_session, dict):
        cart_list = list(cart_session.values())
    elif isinstance(cart_session, list):
        cart_list = cart_session

    products = []
    for prod in raw_products:
        cart_qty = 0
        for item in cart_list:
            if int(item['id']) == prod.id:
                cart_qty = int(item['qty'])
                break
        products.append({
            'id': prod.id,
            'name': prod.name,
            'selling_price': prod.selling_price,
            'stock_quantity': prod.stock_quantity  # Database is already deducted in real-time!
        })

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "add_to_cart":
            p_id = request.POST.get('product')
            qty = int(request.POST.get('quantity'))
            prod = get_object_or_404(Product, id=p_id)
            
            # Real-time Stock Lock: Deduct from DB instantly during standard form add
            if prod.stock_quantity >= qty:
                prod.stock_quantity -= qty
                prod.save()

                # Sync back to session storage dictionary architecture
                if isinstance(cart_session, list):
                    cart_session = {str(item['id']): item for item in cart_session}

                str_id = str(prod.id)
                if str_id in cart_session:
                    cart_session[str_id]['qty'] += qty
                    cart_session[str_id]['total'] = float(cart_session[str_id]['qty']) * float(prod.selling_price)
                else:
                    cart_session[str_id] = {
                        'id': prod.id,
                        'name': prod.name,
                        'qty': qty,
                        'price': float(prod.selling_price),
                        'total': float(prod.selling_price * qty)
                    }
                request.session['cart'] = cart_session
            else:
                messages.error(request, f"⚠️ Not enough stock available for {prod.name}!")
            return redirect('create_bill')

        elif action == "finalize_bill":
            customer = request.POST.get('customer')
            if not cart_list:
                messages.warning(request, "Your cart is empty!")
                return redirect('inventory_list')
            
            try:
                with transaction.atomic():
                    # Link active logged-in user tracking to the finalized bill mapping
                    new_sale = Sale.objects.create(customer_name=customer, user=request.user)
                    total = 0
                    
                    for item in cart_list:
                        prod = Product.objects.get(id=int(item['id']))
                        
                        # CRITICAL SAFEGUARD FIXED: Only creating records. 
                        # DB stock has already been deducted at cart insertion!
                        SaleItem.objects.create(
                            sale=new_sale, 
                            product=prod, 
                            quantity=int(item['qty']), 
                            price_at_sale=float(item['price'])
                        )
                        total += float(item['total'])
                    
                    new_sale.total_amount = total
                    new_sale.save()
                
                # Flush the session cart cleanly upon successful generation
                request.session['cart'] = {}
                messages.success(request, f"Bill saved successfully for {customer}!")
                return redirect('inventory_list')
                
            except Exception as e:
                messages.error(request, f"⚠️ Transaction Declined: {str(e)}")
                return redirect('inventory_list')

    # Compute grand calculations for template rendering metrics
    cart_total = sum(float(i['total']) for i in cart_list)
    return render(request, 'inventory/create_bill.html', {
        'products': products, 
        'cart': cart_list, 
        'cart_total': cart_total
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


# inventory/views.py ke andar purana sales_history isse badlo:
# inventory/views.py ke andar purana sales_history badlo:
@login_required
def sales_history(request):
    """Filters history seamlessly - Admin sees everything, user sees only unarchived logs."""
    if request.user.is_superuser:
        # Admin Rules: Sab kuch dikhao, chahe user ne hide kiya ho ya nahi
        sales = Sale.objects.prefetch_related('items__product').all().order_by('-sale_date')
    else:
        # Ordinary User Rules: Sirf uske banaye hue bills, aur jo usne delete (hide) NA kiye hon
        sales = Sale.objects.prefetch_related('items__product').filter(
            user=request.user, 
            deleted_by_user=False
        ).order_by('-sale_date')
        
    return render(request, 'inventory/sales_history.html', {'sales': sales})# 8. NATIVE COMPATIBLE DOWNLOAD MANAGER
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

# inventory/views.py ke andar purana delete_sale badlo:
# inventory/views.py ke andar delete_sale function ke starting ko aise update karo:

# inventory/views.py ke andar delete_sale function ko badal kar aisa kar do:

# inventory/views.py ke bottom mein delete_sale function ko isse replace karo:

@login_required
def delete_sale(request, sale_id=None, pk=None):
    """
    Handles both permanent Admin purging and User soft-deleting WITHOUT restoring product stock.
    Once a bill is finalized, the stock is gone forever from the physical shop!
    """
    # 1. Resolve active routing parameter keys
    target_id = sale_id or pk or request.GET.get('sale_id')
    sale = get_object_or_404(Sale, id=target_id)

    # Security Guard Validation Layer
    if not request.user.is_superuser and sale.user != request.user:
        messages.error(request, "⚠️ Access Denied: Unauthorized operation tracking parameters!")
        return redirect('sales_history')

    if request.user.is_superuser:
        # ADMIN ACTION: Permanent DB purge configuration
        try:
            with transaction.atomic():
                # FIXED: Loop that restored the stock back to inventory has been REMOVED!
                # We just delete the main sale record. Cascade delete will handle SaleItems cleanly.
                sale.delete()
                messages.success(request, "🗑️ [ADMIN] Bill permanently wiped from records. Inventory stock remains unaffected!")
        except Exception as e:
            messages.error(request, f"❌ Transaction broken execution: {str(e)}")
    else:
        # USER ACTION: Clean Soft Delete logic routing architecture (Hides from user screen only)
        sale.deleted_by_user = True
        sale.save()
        messages.success(request, "🗑️ Bill removed successfully from your active history terminal.")

    return redirect('sales_history')
# 11. CATEGORY FILTER VIEW
# inventory/views.py ke andar category_products function ko replace karo:

# inventory/views.py ke andar category_products function ko isse completely replace karo:

@login_required
def category_products(request, category_id):
    """
    Safely renders targeted category shelf products with full structural check 
    supporting both dictionary and list format cart sessions without crashing.
    """
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category).order_by('name')
    
    # 1. RETRIEVE AND NORMALIZE CART SESSIONS
    cart_session = request.session.get('cart', {})
    
    cart_list = []
    if isinstance(cart_session, dict):
        cart_list = list(cart_session.values())
    elif isinstance(cart_session, list):
        cart_list = cart_session

    # 2. FIXED CRASHING LOOP (LINE 404): Safe iterative genexpr calculation
    cart_total = sum(float(item['total']) for item in cart_list if isinstance(item, dict) and 'total' in item)

    context = {
        'category': category,
        'products': products,
        'cart': cart_list,          # Pass normalized list to template loops
        'cart_total': cart_total,   # Pass computed float total sums
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

# inventory/views.py me in dono functions ko overwrite karein:

@login_required
def add_to_cart_fast(request, product_id):
    """
    Real-time Stock Reservation supporting maximum exact stock clearance boundary limits.
    """
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        try:
            qty_to_add = int(request.POST.get('bulk_qty', 1))
        except ValueError:
            qty_to_add = 1

        # ALLOW GREATER THAN OR EQUAL TO: Supports full clearance (e.g., 20 out of 20)
        if product.stock_quantity >= qty_to_add and qty_to_add > 0:
            product.stock_quantity -= qty_to_add
            product.save()

            # Maintain active structural dictionary representation inside session context
            cart = request.session.get('cart', {})
            str_id = str(product_id)

            if str_id in cart:
                cart[str_id]['qty'] += qty_to_add
                cart[str_id]['total'] = float(cart[str_id]['qty']) * float(cart[str_id]['price'])
            else:
                cart[str_id] = {
                    'id': product.id,
                    'name': product.name,
                    'price': str(product.selling_price),
                    'qty': qty_to_add,
                    'total': float(qty_to_add) * float(product.selling_price)
                }

            request.session['cart'] = cart
            messages.success(request, f"⚡ {product.name} added directly into your billing terminal!")
        else:
            messages.error(request, f"⚠️ Cannot add quantity requested! Stock available: {product.stock_quantity}")

    return redirect(request.META.get('HTTP_REFERER', 'inventory_list'))

@login_required
def remove_from_cart(request, product_id):
    """
    Real-time Stock Restoration: Agar slidebar drawer se item delete (cancel) kiya,
    toh dukan ka maal wapas plus (+) ho jana chahiye!
    """
    cart = request.session.get('cart', {})
    str_id = str(product_id)

    if str_id in cart:
        # 1. Cart me jitni quantity thi use nikal lo
        removed_qty = cart[str_id]['qty']
        
        # 2. Dukan ke original stock me wapas jod (restore) do
        product = get_object_or_404(Product, id=product_id)
        product.stock_quantity += removed_qty
        product.save()

        # 3. Cart se permanently delete karo
        del cart[str_id]
        request.session['cart'] = cart
        messages.success(request, f"🗑️ Item removed successfully. Stock restored back to inventory!")

    return redirect(request.META.get('HTTP_REFERER', 'inventory_list'))

def delete_bill(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    # Galti yahan hai: Ye loop dukan me maal wapas bhar raha hai
    bill.delete()
    return redirect('sales_history')