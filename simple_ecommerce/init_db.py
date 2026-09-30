#!/usr/bin/env python
"""
Database Initializer and Seeder for NovaStore.
Creates all SQLite tables and populates sample products, categories, and demo user.
Works using Python's built-in sqlite3 library with zero external dependencies.
"""
import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')

def hash_password(password):
    """Create a PBKDF2 SHA256 password hash compatible with standard authentication."""
    salt = "codealphasalt"
    h = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"pbkdf2_sha256$100000${salt}${h.hex()}"

def init_database():
    print(f"Initializing database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Django Auth Tables (for seamless Django admin & login compatibility)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auth_user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        password VARCHAR(128) NOT NULL,
        last_login DATETIME,
        is_superuser BOOLEAN NOT NULL,
        username VARCHAR(150) UNIQUE NOT NULL,
        first_name VARCHAR(150) NOT NULL,
        last_name VARCHAR(150) NOT NULL,
        email VARCHAR(254) NOT NULL,
        is_staff BOOLEAN NOT NULL,
        is_active BOOLEAN NOT NULL,
        date_joined DATETIME NOT NULL
    );
    """)

    # 2. Category Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS store_category (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) UNIQUE NOT NULL,
        slug VARCHAR(120) UNIQUE NOT NULL,
        icon VARCHAR(50) NOT NULL,
        description TEXT NOT NULL
    );
    """)

    # 3. Product Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS store_product (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(200) NOT NULL,
        slug VARCHAR(220) UNIQUE NOT NULL,
        description TEXT NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        original_price DECIMAL(10, 2),
        image_url VARCHAR(1000) NOT NULL,
        stock INTEGER NOT NULL,
        is_featured BOOLEAN NOT NULL,
        badge VARCHAR(10) NOT NULL,
        rating DECIMAL(3, 1) NOT NULL,
        reviews_count INTEGER NOT NULL,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        category_id INTEGER NOT NULL REFERENCES store_category (id) ON DELETE CASCADE
    );
    """)

    # 4. Cart Item Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS store_cartitem (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_key VARCHAR(100),
        quantity INTEGER NOT NULL,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        product_id INTEGER NOT NULL REFERENCES store_product (id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES auth_user (id) ON DELETE CASCADE
    );
    """)

    # 5. Order Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS store_order (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number VARCHAR(32) UNIQUE NOT NULL,
        full_name VARCHAR(150) NOT NULL,
        email VARCHAR(254) NOT NULL,
        phone VARCHAR(25) NOT NULL,
        address VARCHAR(250) NOT NULL,
        city VARCHAR(100) NOT NULL,
        state VARCHAR(100) NOT NULL,
        postal_code VARCHAR(20) NOT NULL,
        country VARCHAR(100) NOT NULL,
        payment_method VARCHAR(20) NOT NULL,
        shipping_fee DECIMAL(6, 2) NOT NULL,
        total_amount DECIMAL(10, 2) NOT NULL,
        status VARCHAR(20) NOT NULL,
        notes TEXT NOT NULL,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        user_id INTEGER REFERENCES auth_user (id) ON DELETE SET NULL
    );
    """)

    # 6. OrderItem Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS store_orderitem (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name VARCHAR(200) NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        quantity INTEGER NOT NULL,
        order_id INTEGER NOT NULL REFERENCES store_order (id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES store_product (id) ON DELETE SET NULL
    );
    """)

    # Populate Categories
    categories = [
        ('Electronics', 'electronics', 'bi-laptop', 'Computers, displays, and audio gear.'),
        ('Fashion & Apparel', 'fashion', 'bi-bag', 'Trendy clothing, accessories, and shoes.'),
        ('Home & Living', 'home-living', 'bi-house-door', 'Furniture, lighting, and everyday essentials.'),
        ('Books & Stationery', 'books', 'bi-book', 'Best-selling books, notebooks, and learning materials.'),
        ('Wearables & Audio', 'wearables', 'bi-smartwatch', 'Smartwatches, headphones, and wireless earbuds.')
    ]

    for name, slug, icon, desc in categories:
        cursor.execute("SELECT id FROM store_category WHERE slug = ?", (slug,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO store_category (name, slug, icon, description) VALUES (?, ?, ?, ?)",
                (name, slug, icon, desc)
            )

    # Populate Products
    cursor.execute("SELECT slug, id FROM store_category")
    cat_map = {row[0]: row[1] for row in cursor.fetchall()}
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    products = [
        (
            'AeroSound Pro Noise-Cancelling Headphones',
            'aerosound-pro-headphones',
            'Experience studio-grade acoustics with advanced active noise cancellation, 40-hour battery life, plush memory foam ear cushions, and ultra-fast USB-C charging.',
            199.99, 249.99,
            'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80',
            25, 1, 'HOT', 4.9, 128, now, now, cat_map.get('wearables', 1)
        ),
        (
            'UltraSlim 4K Touchscreen Laptop 15"',
            'ultraslim-4k-touchscreen-laptop',
            'Engineered for creators and professionals. Features an edge-to-edge 4K OLED display, 16GB RAM, 1TB NVMe SSD, and whisper-quiet dual cooling fans.',
            899.99, 1099.99,
            'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80',
            12, 1, 'SALE', 4.8, 84, now, now, cat_map.get('electronics', 1)
        ),
        (
            'PulseFit Horizon Smart Fitness Watch',
            'pulsefit-smart-watch',
            'Track heart rate, sleep stages, SpO2, and GPS workouts in real-time. Water resistant up to 50 meters with vibrant AMOLED always-on display.',
            129.50, 159.99,
            'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80',
            30, 1, 'NEW', 4.7, 92, now, now, cat_map.get('wearables', 1)
        ),
        (
            'Classic Minimalist Leather Backpack',
            'classic-leather-backpack',
            'Handcrafted from full-grain vintage leather with padded laptop sleeve, brass zippers, and breathable shoulder straps. Built to last for daily commute and travel.',
            79.99, 99.99,
            'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80',
            18, 0, '', 4.6, 45, now, now, cat_map.get('fashion', 2)
        ),
        (
            'Nordic Ceramic Coffee Mug Set (4-Piece)',
            'nordic-ceramic-coffee-mug-set',
            'Artisan stoneware mugs with matte glaze finish and ergonomic handle. Dishwasher, microwave, and oven safe for your morning espresso and latte rituals.',
            34.99, 42.00,
            'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800&q=80',
            40, 0, 'SALE', 4.8, 67, now, now, cat_map.get('home-living', 3)
        ),
        (
            'Wireless Ergonomic Mechanical Keyboard',
            'wireless-ergonomic-mechanical-keyboard',
            'Hot-swappable tactile switches, RGB per-key backlighting, Bluetooth 5.2 multi-device connectivity, and customizable programmable macro keys.',
            119.00, 139.00,
            'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&q=80',
            15, 1, 'HOT', 4.9, 110, now, now, cat_map.get('electronics', 1)
        ),
        (
            'Modern Hardcover Bullet Journal & Pen',
            'modern-hardcover-bullet-journal',
            '160 GSM ultra-thick bleedproof dotted pages with expandable inner pocket, two ribbon bookmarks, and a precision brass rollerball gel pen.',
            22.50, 28.00,
            'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&q=80',
            50, 0, '', 4.7, 38, now, now, cat_map.get('books', 4)
        ),
        (
            'Minimalist Polarized Sunglasses UV400',
            'minimalist-polarized-sunglasses',
            'Lightweight titanium frame with polarized glare-reducing lenses and complete UV400 protection. Includes magnetic leather travel case and microfiber cloth.',
            49.99, 65.00,
            'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=800&q=80',
            22, 0, 'NEW', 4.5, 29, now, now, cat_map.get('fashion', 2)
        ),
        (
            'Aroma Warm Mist Essential Oil Diffuser',
            'aroma-warm-mist-diffuser',
            'Ultrasonic 500ml ultrasonic humidifier with 7 soothing ambient LED colors, timer settings, auto-shutoff protection, and ultra-quiet whisper operation.',
            38.99, 49.99,
            'https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=800&q=80',
            35, 0, '', 4.6, 53, now, now, cat_map.get('home-living', 3)
        ),
    ]

    for p in products:
        cursor.execute("SELECT id FROM store_product WHERE slug = ?", (p[1],))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO store_product (
                name, slug, description, price, original_price, image_url,
                stock, is_featured, badge, rating, reviews_count, created_at, updated_at, category_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, p)

    # Seed Demo Users
    cursor.execute("SELECT id FROM auth_user WHERE username = 'demouser'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO auth_user (
            password, is_superuser, username, first_name, last_name,
            email, is_staff, is_active, date_joined
        ) VALUES (?, 0, 'demouser', 'Alex', 'Morgan', 'demo@store.com', 0, 1, ?)
        """, (hash_password('demo12345'), now))

    cursor.execute("SELECT id FROM auth_user WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO auth_user (
            password, is_superuser, username, first_name, last_name,
            email, is_staff, is_active, date_joined
        ) VALUES (?, 1, 'admin', 'Store', 'Administrator', 'admin@store.com', 1, 1, ?)
        """, (hash_password('admin12345'), now))

    conn.commit()
    conn.close()
    print("Database initialization and seeding completed successfully!")

if __name__ == '__main__':
    init_database()
