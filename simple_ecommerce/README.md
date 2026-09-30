# NovaStore - Simple E-Commerce Store
**CodeAlpha Internship — Task 1 Web Development Project**  
Website: [www.codealpha.tech](https://www.codealpha.tech)

---

## 📌 Project Overview
NovaStore is a modern, responsive, full-stack e-commerce web application featuring:
- **Dynamic Product Catalog**: Browse products across categories (Electronics, Fashion, Home & Living, Books, Wearables) with search and price/rating sorting.
- **Product Details Page**: High-resolution image showcases, stock indicator, feature highlights, user ratings, and dynamic quantity selector.
- **Shopping Cart**: Real-time AJAX item additions, cart badge counter, quantity increment/decrement, line-item totals, tax calculation, and free shipping threshold.
- **Checkout & Order Processing**: Complete checkout flow with shipping address capture, payment method selection, order placement, and automatic stock deduction.
- **Order Confirmation & Invoicing**: Detailed receipt with generated order numbers (`#ORD-XXXX`), itemized breakdown, and print invoice button.
- **User Authentication & Profiles**: User registration, login/logout, session preservation (guest cart transfers to user cart on login), and **Order History** dashboard.
- **Dual-Mode Backend Execution**:
  1. **Full Django Mode** (Standard Django 5 MVC architecture with models, migrations, views, admin panel).
  2. **Instant Zero-Dependency Mode** (`python standalone_server.py`) for immediate one-click testing without running any `pip install`!

---

## 🛠️ Technology Stack
- **Frontend**: HTML5, CSS3 (Custom properties, responsive grid/flexbox), JavaScript (ES6+ AJAX Fetch API), Bootstrap 5.3, Bootstrap Icons
- **Backend**: Python 3 / Django 5 (or built-in `http.server` & `sqlite3`)
- **Database**: SQLite3 (`db.sqlite3` included and pre-seeded with sample products and demo user accounts)

---

## 🚀 How to Run the Project

### Option A: Instant Run (Zero Dependencies Required)
You can run the store immediately using Python's built-in libraries with zero setup:
```bash
python standalone_server.py
```
Open your browser and navigate to:  
👉 **`http://localhost:8000`**

---

### Option B: Run with Django
If you prefer running via the Django framework:

1. **(Optional) Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Apply database migrations**:
   ```bash
   python manage.py migrate
   ```

4. **(Optional) Seed sample products & users**:
   ```bash
   python manage.py seed_products
   ```

5. **Start the Django development server**:
   ```bash
   python manage.py runserver
   ```
   Open your browser at: **`http://127.0.0.1:8000/`**  
   Admin Panel at: **`http://127.0.0.1:8000/admin/`**

---

## 🔑 Demo Login Credentials

| Role | Username | Password | Purpose |
|------|----------|----------|---------|
| **Demo Customer** | `demouser` | `demo12345` | Test shopping cart, checkout, order history |
| **Store Admin** | `admin` | `admin12345` | Access Django Admin panel to manage products & orders |

*You can also click **Register** to create any new user account.*

---

## 📂 Project Structure
```
simple_ecommerce/
├── ecommerce_project/         # Django Project Settings & Configuration
│   ├── __init__.py
│   ├── settings.py           # App settings, templates, static config
│   ├── urls.py               # Main URL router
│   ├── wsgi.py
│   └── asgi.py
├── store/                     # Main Store Application
│   ├── models.py             # Category, Product, CartItem, Order, OrderItem
│   ├── views.py              # Catalog, detail, cart, checkout, orders, auth
│   ├── urls.py               # Store route definitions
│   ├── forms.py              # Registration & Checkout forms
│   ├── admin.py              # Django admin registrations
│   ├── context_processors.py # Global cart count & category injector
│   ├── migrations/           # Database migration files
│   └── management/commands/  # Seeder command (seed_products.py)
├── templates/                 # Clean HTML5 Templates
│   ├── base.html             # Common navbar, footer, toasts, cart badge
│   ├── store/
│   │   ├── product_list.html # Hero banner, category tabs, product grid
│   │   ├── product_detail.html # Product details, gallery, qty stepper
│   │   ├── cart.html         # Interactive cart table & totals
│   │   ├── checkout.html     # Shipping form & payment selector
│   │   ├── order_success.html# Order confirmation receipt & invoice
│   │   └── order_history.html# User order tracking
│   └── accounts/
│       ├── login.html        # Sign in form
│       └── register.html     # Registration form
├── static/
│   ├── css/style.css         # Modern styling, animations, cards, badges
│   └── js/main.js            # AJAX cart addition, toasts, badge updates
├── standalone_server.py       # Instant zero-install Python server
├── init_db.py                 # SQLite database generator & seeder
├── db.sqlite3                 # Pre-configured SQLite database
├── test_store.py              # Automated backend test suite
├── requirements.txt           # Dependency specifications
└── README.md                  # Project documentation
```

---

## ✨ Features Checklist
- [x] Product listings with categories, filters, and search
- [x] Product details page with image preview and full specifications
- [x] Shopping cart with quantity updates and item removal
- [x] User registration, login, and logout
- [x] Order checkout and processing with address & payment capture
- [x] Order confirmation receipt with order ID and invoice breakdown
- [x] Order history dashboard for registered users
- [x] SQLite database storing products, categories, cart items, users, and orders
- [x] Responsive layout for mobile, tablet, and desktop
