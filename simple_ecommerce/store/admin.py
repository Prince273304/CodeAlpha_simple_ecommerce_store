from django.contrib import admin
from .models import Category, Product, CartItem, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'original_price', 'stock', 'is_featured', 'badge', 'rating']
    list_filter = ['category', 'is_featured', 'badge', 'created_at']
    list_editable = ['price', 'stock', 'is_featured', 'badge']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'email', 'total_amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'full_name', 'email', 'phone']
    inlines = [OrderItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'user', 'session_key', 'created_at']
