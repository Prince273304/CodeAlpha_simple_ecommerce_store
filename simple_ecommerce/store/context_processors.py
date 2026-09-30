from .models import Category, CartItem


def cart_context(request):
    """Context processor to supply cart item count and categories globally."""
    categories = Category.objects.all()
    cart_count = 0
    
    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user)
    else:
        session_key = request.session.session_key
        if session_key:
            items = CartItem.objects.filter(session_key=session_key)
        else:
            items = []

    for item in items:
        cart_count += item.quantity

    return {
        'global_categories': categories,
        'cart_count': cart_count,
    }
