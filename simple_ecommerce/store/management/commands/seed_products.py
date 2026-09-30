from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Category, Product


class Command(BaseCommand):
    help = 'Seeds initial sample products, categories, and demo user accounts'

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories...")
        categories_data = [
            {'name': 'Electronics', 'slug': 'electronics', 'icon': 'bi-laptop', 'description': 'Computers, audio, and high-tech gadgets.'},
            {'name': 'Fashion & Apparel', 'slug': 'fashion', 'icon': 'bi-bag', 'description': 'Trendy clothing, accessories, and shoes.'},
            {'name': 'Home & Living', 'slug': 'home-living', 'icon': 'bi-house-door', 'description': 'Furniture, lighting, and kitchen essentials.'},
            {'name': 'Books & Stationery', 'slug': 'books', 'icon': 'bi-book', 'description': 'Best-sellers, notebooks, and learning materials.'},
            {'name': 'Wearables & Audio', 'slug': 'wearables', 'icon': 'bi-smartwatch', 'description': 'Smartwatches, headphones, and earbuds.'},
        ]

        categories = {}
        for cdata in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=cdata['slug'],
                defaults={'name': cdata['name'], 'icon': cdata['icon'], 'description': cdata['description']}
            )
            categories[cdata['slug']] = cat

        self.stdout.write("Seeding products...")
        products_data = [
            {
                'name': 'AeroSound Pro Noise-Cancelling Headphones',
                'slug': 'aerosound-pro-headphones',
                'category': categories['wearables'],
                'description': 'Experience studio-grade acoustics with advanced active noise cancellation, 40-hour battery life, plush memory foam ear cushions, and ultra-fast USB-C charging.',
                'price': Decimal('199.99'),
                'original_price': Decimal('249.99'),
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80',
                'stock': 25,
                'is_featured': True,
                'badge': 'HOT',
                'rating': Decimal('4.9'),
                'reviews_count': 128,
            },
            {
                'name': 'UltraSlim 4K Touchscreen Laptop 15"',
                'slug': 'ultraslim-4k-touchscreen-laptop',
                'category': categories['electronics'],
                'description': 'Engineered for creators and professionals. Features an edge-to-edge 4K OLED display, 16GB RAM, 1TB NVMe SSD, and whisper-quiet dual cooling fans.',
                'price': Decimal('899.99'),
                'original_price': Decimal('1099.99'),
                'image_url': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80',
                'stock': 12,
                'is_featured': True,
                'badge': 'SALE',
                'rating': Decimal('4.8'),
                'reviews_count': 84,
            },
            {
                'name': 'PulseFit Horizon Smart Fitness Watch',
                'slug': 'pulsefit-smart-watch',
                'category': categories['wearables'],
                'description': 'Track heart rate, sleep stages, SpO2, and GPS workouts in real-time. Water resistant up to 50 meters with vibrant AMOLED always-on display.',
                'price': Decimal('129.50'),
                'original_price': Decimal('159.99'),
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80',
                'stock': 30,
                'is_featured': True,
                'badge': 'NEW',
                'rating': Decimal('4.7'),
                'reviews_count': 92,
            },
            {
                'name': 'Classic Minimalist Leather Backpack',
                'slug': 'classic-leather-backpack',
                'category': categories['fashion'],
                'description': 'Handcrafted from full-grain vintage leather with padded laptop sleeve, brass zippers, and breathable shoulder straps. Built to last for daily commute and travel.',
                'price': Decimal('79.99'),
                'original_price': Decimal('99.99'),
                'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80',
                'stock': 18,
                'is_featured': False,
                'badge': '',
                'rating': Decimal('4.6'),
                'reviews_count': 45,
            },
            {
                'name': 'Nordic Ceramic Coffee Mug Set (4-Piece)',
                'slug': 'nordic-ceramic-coffee-mug-set',
                'category': categories['home-living'],
                'description': 'Artisan stoneware mugs with matte glaze finish and ergonomic handle. Dishwasher, microwave, and oven safe for your morning espresso and latte rituals.',
                'price': Decimal('34.99'),
                'original_price': Decimal('42.00'),
                'image_url': 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800&q=80',
                'stock': 40,
                'is_featured': False,
                'badge': 'SALE',
                'rating': Decimal('4.8'),
                'reviews_count': 67,
            },
            {
                'name': 'Wireless Ergonomic Mechanical Keyboard',
                'slug': 'wireless-ergonomic-mechanical-keyboard',
                'category': categories['electronics'],
                'description': 'Hot-swappable tactile switches, RGB per-key backlighting, Bluetooth 5.2 multi-device connectivity, and customizable programmable macro keys.',
                'price': Decimal('119.00'),
                'original_price': Decimal('139.00'),
                'image_url': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&q=80',
                'stock': 15,
                'is_featured': True,
                'badge': 'HOT',
                'rating': Decimal('4.9'),
                'reviews_count': 110,
            },
            {
                'name': 'Modern Hardcover Bullet Journal & Pen',
                'slug': 'modern-hardcover-bullet-journal',
                'category': categories['books'],
                'description': '160 GSM ultra-thick bleedproof dotted pages with expandable inner pocket, two ribbon bookmarks, and a precision brass rollerball gel pen.',
                'price': Decimal('22.50'),
                'original_price': Decimal('28.00'),
                'image_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&q=80',
                'stock': 50,
                'is_featured': False,
                'badge': '',
                'rating': Decimal('4.7'),
                'reviews_count': 38,
            },
            {
                'name': 'Minimalist Polarized Sunglasses UV400',
                'slug': 'minimalist-polarized-sunglasses',
                'category': categories['fashion'],
                'description': 'Lightweight titanium frame with polarized glare-reducing lenses and complete UV400 protection. Includes magnetic leather travel case and microfiber cloth.',
                'price': Decimal('49.99'),
                'original_price': Decimal('65.00'),
                'image_url': 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=800&q=80',
                'stock': 22,
                'is_featured': False,
                'badge': 'NEW',
                'rating': Decimal('4.5'),
                'reviews_count': 29,
            },
            {
                'name': 'Aroma Warm Mist Essential Oil Diffuser',
                'slug': 'aroma-warm-mist-diffuser',
                'category': categories['home-living'],
                'description': 'Ultrasonic 500ml ultrasonic humidifier with 7 soothing ambient LED colors, timer settings, auto-shutoff protection, and ultra-quiet whisper operation.',
                'price': Decimal('38.99'),
                'original_price': Decimal('49.99'),
                'image_url': 'https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=800&q=80',
                'stock': 35,
                'is_featured': False,
                'badge': '',
                'rating': Decimal('4.6'),
                'reviews_count': 53,
            },
        ]

        for pdata in products_data:
            Product.objects.get_or_create(
                slug=pdata['slug'],
                defaults=pdata
            )

        self.stdout.write("Creating demo accounts...")
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@store.com', 'admin12345')
            self.stdout.write("Created superuser: admin / admin12345")

        if not User.objects.filter(username='demouser').exists():
            u = User.objects.create_user('demouser', 'demo@store.com', 'demo12345')
            u.first_name = 'Alex'
            u.last_name = 'Morgan'
            u.save()
            self.stdout.write("Created demo user: demouser / demo12345")

        self.stdout.write(self.style.SUCCESS("Successfully seeded database!"))
