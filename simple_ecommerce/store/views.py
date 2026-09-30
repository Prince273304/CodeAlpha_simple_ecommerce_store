from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import Category, Product, CartItem, Order, OrderItem
from .forms import UserRegistrationForm, CheckoutForm


def _get_session_key(request):
    """Ensure session key exists for guest cart tracking."""
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _get_cart_items(request):
    """Retrieve cart items for either logged-in user or guest session."""
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user)
    session_key = _get_session_key(request)
    return CartItem.objects.filter(session_key=session_key)


def _transfer_guest_cart_to_user(request, user):
    """Transfer items from guest session cart to the logged-in user's cart."""
    session_key = request.session.session_key
    if session_key:
        guest_items = CartItem.objects.filter(session_key=session_key)
        for item in guest_items:
            existing_user_item = CartItem.objects.filter(user=user, product=item.product).first()
            if existing_user_item:
                existing_user_item.quantity += item.quantity
                existing_user_item.save()
                item.delete()
            else:
                item.user = user
                item.session_key = None
                item.save()


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.all()

    # Category filter
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Search filter
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Sorting
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'rating':
        products = products.order_by('-rating')
    elif sort == 'popular':
        products = products.order_by('-reviews_count')
    else:
        products = products.order_by('-created_at')

    featured_products = Product.objects.filter(is_featured=True)[:4]

    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'query': query,
        'sort': sort,
        'featured_products': featured_products,
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)


def cart_view(request):
    cart_items = _get_cart_items(request)
    subtotal = sum(item.subtotal for item in cart_items)
    
    # Free shipping if subtotal >= $50, else $5.00 flat (free if cart is empty)
    if subtotal == 0 or subtotal >= Decimal('50.00'):
        shipping_fee = Decimal('0.00')
    else:
        shipping_fee = Decimal('5.00')

    estimated_tax = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))
    total = subtotal + shipping_fee + estimated_tax

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'estimated_tax': estimated_tax,
        'total': total,
    }
    return render(request, 'store/cart.html', context)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if quantity < 1:
        quantity = 1

    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
    else:
        session_key = _get_session_key(request)
        cart_item, created = CartItem.objects.get_or_create(
            session_key=session_key,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

    # Total cart count for client badges
    all_items = _get_cart_items(request)
    cart_count = sum(i.quantity for i in all_items)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'message': f'"{product.name}" added to cart!',
            'cart_count': cart_count,
            'product_name': product.name
        })

    messages.success(request, f'Added "{product.name}" to your cart.')
    next_url = request.POST.get('next') or request.GET.get('next') or 'cart'
    return redirect(next_url)


def update_cart(request, item_id):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    else:
        session_key = _get_session_key(request)
        cart_item = get_object_or_404(CartItem, id=item_id, session_key=session_key)

    action = request.POST.get('action') or request.GET.get('action')
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    elif 'quantity' in request.POST:
        qty = int(request.POST.get('quantity', 1))
        if qty > 0:
            cart_item.quantity = qty
            cart_item.save()
        else:
            cart_item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        all_items = _get_cart_items(request)
        subtotal = sum(item.subtotal for item in all_items)
        cart_count = sum(i.quantity for i in all_items)
        return JsonResponse({
            'success': True,
            'cart_count': cart_count,
            'subtotal': float(subtotal)
        })

    return redirect('cart')


def remove_from_cart(request, item_id):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    else:
        session_key = _get_session_key(request)
        cart_item = get_object_or_404(CartItem, id=item_id, session_key=session_key)

    product_name = cart_item.product.name
    cart_item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        all_items = _get_cart_items(request)
        subtotal = sum(item.subtotal for item in all_items)
        cart_count = sum(i.quantity for i in all_items)
        return JsonResponse({
            'success': True,
            'message': f'"{product_name}" removed from cart.',
            'cart_count': cart_count,
            'subtotal': float(subtotal)
        })

    messages.info(request, f'Removed "{product_name}" from your cart.')
    return redirect('cart')


def checkout_view(request):
    cart_items = _get_cart_items(request)
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Please add products before checking out.")
        return redirect('product_list')

    subtotal = sum(item.subtotal for item in cart_items)
    shipping_fee = Decimal('0.00') if subtotal >= Decimal('50.00') else Decimal('5.00')
    estimated_tax = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))
    total = subtotal + shipping_fee + estimated_tax

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.shipping_fee = shipping_fee
            order.total_amount = total
            order.save()

            # Create OrderItems & update stock
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    price=item.product.price,
                    quantity=item.quantity
                )
                if item.product.stock >= item.quantity:
                    item.product.stock -= item.quantity
                    item.product.save()

            # Clear cart
            cart_items.delete()

            messages.success(request, f"Order #{order.order_number} placed successfully!")
            return redirect('order_success', order_number=order.order_number)
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                'email': request.user.email,
            }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'estimated_tax': estimated_tax,
        'total': total,
    }
    return render(request, 'store/checkout.html', context)


def order_success_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'store/order_success.html', {'order': order})


@login_required
def order_history_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('product_list')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            _transfer_guest_cart_to_user(request, user)
            messages.success(request, f"Welcome to our store, {user.username}! Your account was created successfully.")
            return redirect('product_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('product_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            _transfer_guest_cart_to_user(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next') or 'product_list'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('product_list')
