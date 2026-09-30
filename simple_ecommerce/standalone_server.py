#!/usr/bin/env python
"""
NovaStore - Standalone Zero-Dependency Runner
Runs a complete full-stack web server using Python's built-in libraries (http.server, sqlite3).
Provides full e-commerce functionality:
- Product Catalog, Categories, Search, and Sorting
- Product Details Page with Reviews and Stock Status
- Real-time Shopping Cart (Add, Update Quantity, Remove)
- Checkout & Order Processing with Order Receipt
- User Authentication (Register, Login, Logout) & Order History
- Serves CSS, JS, and Images
No 'pip install' required!
"""
import http.server
import socketserver
import urllib.parse
import json
import sqlite3
import os
import re
import uuid
import mimetypes
from datetime import datetime
from decimal import Decimal

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'db.sqlite3')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# In-memory sessions: session_id -> { 'user_id': int, 'username': str, 'messages': list }
SESSIONS = {}

class NovaStoreHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Clean logging
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]} - {args[1]}")

    def get_session(self):
        cookies_header = self.headers.get('Cookie', '')
        session_id = None
        for cookie in cookies_header.split(';'):
            cookie = cookie.strip()
            if cookie.startswith('novastore_session='):
                session_id = cookie.split('=', 1)[1]
                break
        
        if not session_id or session_id not in SESSIONS:
            session_id = str(uuid.uuid4())
            SESSIONS[session_id] = {
                'user_id': None,
                'username': None,
                'messages': []
            }
        self.session_id = session_id
        return SESSIONS[session_id]

    def send_html(self, html_content, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Set-Cookie', f'novastore_session={self.session_id}; Path=/; HttpOnly; SameSite=Lax')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Set-Cookie', f'novastore_session={self.session_id}; Path=/; HttpOnly; SameSite=Lax')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def redirect(self, location):
        self.send_response(303)
        self.send_header('Location', location)
        self.send_header('Set-Cookie', f'novastore_session={self.session_id}; Path=/; HttpOnly; SameSite=Lax')
        self.end_headers()

    def get_cart_count(self, session):
        conn = get_db()
        cur = conn.cursor()
        if session.get('user_id'):
            cur.execute("SELECT SUM(quantity) FROM store_cartitem WHERE user_id = ?", (session['user_id'],))
        else:
            cur.execute("SELECT SUM(quantity) FROM store_cartitem WHERE session_key = ?", (self.session_id,))
        res = cur.fetchone()[0]
        conn.close()
        return res if res else 0

    def get_categories(self):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM store_category ORDER BY name ASC")
        cats = [dict(r) for r in cur.fetchall()]
        conn.close()
        return cats

    def render_layout(self, title, content_html, session):
        categories = self.get_categories()
        cart_count = self.get_cart_count(session)
        is_auth = bool(session.get('user_id'))
        username = session.get('username', '')

        cat_dropdown_html = ""
        footer_cats_html = ""
        for cat in categories:
            cat_dropdown_html += f"""
            <li>
                <a class="dropdown-item d-flex align-items-center gap-2" href="/category/{cat['slug']}">
                    <i class="bi {cat['icon']} text-primary"></i> {cat['name']}
                </a>
            </li>"""
            footer_cats_html += f"""
            <li><a href="/category/{cat['slug']}" class="text-secondary text-decoration-none">{cat['name']}</a></li>"""

        # Auth Nav items
        if is_auth:
            auth_nav_html = f"""
            <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle d-flex align-items-center gap-1 fw-medium" href="#" role="button" data-bs-toggle="dropdown">
                    <i class="bi bi-person-circle fs-5 text-primary"></i>
                    <span>{username}</span>
                </a>
                <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0">
                    <li class="px-3 py-1 small text-muted">Signed in as <strong>{username}</strong></li>
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item" href="/orders"><i class="bi bi-receipt me-2"></i>My Orders</a></li>
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item text-danger" href="/logout"><i class="bi bi-box-arrow-right me-2"></i>Log Out</a></li>
                </ul>
            </li>"""
        else:
            auth_nav_html = """
            <li class="nav-item"><a class="nav-link fw-medium" href="/login">Log In</a></li>
            <li class="nav-item"><a class="btn btn-outline-primary btn-sm rounded-pill px-3" href="/register">Register</a></li>
            """

        # Flash messages
        messages_html = ""
        if session.get('messages'):
            for msg_type, msg_text in session['messages']:
                messages_html += f"""
                <div class="alert alert-{msg_type} alert-dismissible fade show shadow-sm d-flex align-items-center gap-2" role="alert">
                    <i class="bi bi-info-circle-fill"></i>
                    <div>{msg_text}</div>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>"""
            session['messages'] = []

        badge_class = "" if cart_count > 0 else "d-none"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - NovaStore</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body class="d-flex flex-column min-vh-100">

    <div class="top-bar py-1 bg-dark text-white text-center small">
        <span>✨ Free express shipping on all orders over $50! CodeAlpha Task 1 Demo Store</span>
    </div>

    <nav class="navbar navbar-expand-lg navbar-light bg-white sticky-top shadow-sm py-3">
        <div class="container">
            <a class="navbar-brand d-flex align-items-center gap-2" href="/">
                <div class="brand-icon"><i class="bi bi-bag-heart-fill"></i></div>
                <span class="brand-text">Nova<strong>Store</strong></span>
            </a>

            <button class="navbar-toggler border-0 shadow-none" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarContent">
                <form class="d-flex mx-lg-auto my-2 my-lg-0 search-form" action="/" method="GET">
                    <div class="input-group">
                        <span class="input-group-text bg-light border-end-0"><i class="bi bi-search text-muted"></i></span>
                        <input class="form-control bg-light border-start-0 ps-0" type="search" name="q" placeholder="Search products, brands, categories...">
                        <button class="btn btn-primary px-3" type="submit">Search</button>
                    </div>
                </form>

                <ul class="navbar-nav ms-auto align-items-center gap-2 pt-2 pt-lg-0">
                    <li class="nav-item">
                        <a class="nav-link fw-medium" href="/"><i class="bi bi-grid me-1"></i> Catalog</a>
                    </li>
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle fw-medium" href="#" role="button" data-bs-toggle="dropdown">Categories</a>
                        <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0">
                            <li><a class="dropdown-item" href="/">All Products</a></li>
                            <li><hr class="dropdown-divider"></li>
                            {cat_dropdown_html}
                        </ul>
                    </li>
                    {auth_nav_html}
                    <li class="nav-item ms-lg-2">
                        <a href="/cart" class="btn btn-light rounded-pill position-relative px-3 py-2 border cart-btn">
                            <i class="bi bi-cart3 fs-5"></i>
                            <span class="ms-1 d-none d-md-inline fw-semibold">Cart</span>
                            <span id="cart-badge" class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger shadow-sm {badge_class}">
                                {cart_count}
                            </span>
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-3">
        {messages_html}
    </div>

    <main class="flex-grow-1">
        {content_html}
    </main>

    <div class="toast-container position-fixed bottom-0 end-0 p-3" style="z-index: 1090;">
        <div id="cartToast" class="toast align-items-center text-bg-dark border-0 shadow-lg" role="alert">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center gap-2">
                    <i class="bi bi-check-circle-fill text-success fs-5"></i>
                    <span id="toastMessage">Item added to your shopping cart.</span>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white pt-5 pb-4 mt-5">
        <div class="container">
            <div class="row g-4">
                <div class="col-lg-4 col-md-6">
                    <div class="d-flex align-items-center gap-2 mb-3">
                        <div class="brand-icon"><i class="bi bi-bag-heart-fill"></i></div>
                        <span class="brand-text text-white">Nova<strong>Store</strong></span>
                    </div>
                    <p class="text-secondary small mb-3">
                        A full-featured, responsive e-commerce web application featuring real-time cart interactions, dynamic product catalog, multi-category browsing, and end-to-end checkout processing.
                    </p>
                    <div class="text-secondary small">
                        Developed for <strong>CodeAlpha Internship</strong> — Task 1.
                    </div>
                </div>

                <div class="col-lg-2 col-md-6">
                    <h6 class="text-uppercase fw-bold mb-3 text-light">Quick Links</h6>
                    <ul class="list-unstyled text-secondary small d-flex flex-column gap-2">
                        <li><a href="/" class="text-secondary text-decoration-none">All Products</a></li>
                        <li><a href="/cart" class="text-secondary text-decoration-none">Shopping Cart</a></li>
                        <li><a href="/orders" class="text-secondary text-decoration-none">My Orders</a></li>
                        <li><a href="https://www.codealpha.tech" target="_blank" class="text-secondary text-decoration-none">www.codealpha.tech</a></li>
                    </ul>
                </div>

                <div class="col-lg-3 col-md-6">
                    <h6 class="text-uppercase fw-bold mb-3 text-light">Categories</h6>
                    <ul class="list-unstyled text-secondary small d-flex flex-column gap-2">
                        {footer_cats_html}
                    </ul>
                </div>

                <div class="col-lg-3 col-md-6">
                    <h6 class="text-uppercase fw-bold mb-3 text-light">Store Features</h6>
                    <ul class="list-unstyled text-secondary small d-flex flex-column gap-2">
                        <li><i class="bi bi-shield-check text-success me-2"></i>Secure Checkout</li>
                        <li><i class="bi bi-truck text-primary me-2"></i>Fast Express Delivery</li>
                        <li><i class="bi bi-arrow-repeat text-warning me-2"></i>30-Day Easy Returns</li>
                        <li><i class="bi bi-headset text-info me-2"></i>24/7 Customer Support</li>
                    </ul>
                </div>
            </div>

            <hr class="border-secondary my-4">

            <div class="row align-items-center small text-secondary">
                <div class="col-md-6 text-center text-md-start mb-2 mb-md-0">
                    &copy; 2026 NovaStore. Built for CodeAlpha Internship Task 1.
                </div>
                <div class="col-md-6 text-center text-md-end">
                    <span class="badge bg-secondary me-2">Python & SQLite</span>
                    <span class="badge bg-secondary me-2">HTML5 / CSS3</span>
                    <span class="badge bg-secondary">JavaScript</span>
                </div>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/main.js"></script>
</body>
</html>"""
        return html

    def do_GET(self):
        session = self.get_session()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Serve static files
        if path.startswith('/static/'):
            filepath = os.path.join(BASE_DIR, path.lstrip('/'))
            if os.path.exists(filepath) and os.path.isfile(filepath):
                mime_type, _ = mimetypes.guess_type(filepath)
                self.send_response(200)
                self.send_header('Content-Type', mime_type or 'application/octet-stream')
                self.end_headers()
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "Static file not found")
                return

        # 1. Product Catalog Home / Category View
        if path == '/' or path == '/catalog' or path.startswith('/category/'):
            category_slug = None
            if path.startswith('/category/'):
                category_slug = path.split('/')[2]

            search_query = query.get('q', [''])[0].strip()
            sort = query.get('sort', ['newest'])[0]

            conn = get_db()
            cur = conn.cursor()

            sql = """
            SELECT p.*, c.name as category_name, c.slug as category_slug
            FROM store_product p
            JOIN store_category c ON p.category_id = c.id
            WHERE 1=1
            """
            params = []

            if category_slug:
                sql += " AND c.slug = ?"
                params.append(category_slug)

            if search_query:
                sql += " AND (p.name LIKE ? OR p.description LIKE ? OR c.name LIKE ?)"
                kw = f"%{search_query}%"
                params.extend([kw, kw, kw])

            if sort == 'price_asc':
                sql += " ORDER BY p.price ASC"
            elif sort == 'price_desc':
                sql += " ORDER BY p.price DESC"
            elif sort == 'rating':
                sql += " ORDER BY p.rating DESC"
            elif sort == 'popular':
                sql += " ORDER BY p.reviews_count DESC"
            else:
                sql += " ORDER BY p.id DESC"

            cur.execute(sql, params)
            products = [dict(r) for r in cur.fetchall()]

            # Active category
            active_cat = None
            if category_slug:
                cur.execute("SELECT * FROM store_category WHERE slug = ?", (category_slug,))
                row = cur.fetchone()
                if row:
                    active_cat = dict(row)

            categories = self.get_categories()
            conn.close()

            # Build Hero
            hero_html = ""
            if not search_query and not category_slug:
                hero_html = """
                <section class="hero-banner py-5 mb-5 bg-gradient-primary text-white position-relative overflow-hidden">
                    <div class="container position-relative py-4" style="z-index: 2;">
                        <div class="row align-items-center g-4">
                            <div class="col-lg-7 text-center text-lg-start">
                                <span class="badge bg-white text-primary rounded-pill px-3 py-2 fw-bold text-uppercase mb-3 shadow-sm">
                                    🚀 Summer Tech & Lifestyle Deals
                                </span>
                                <h1 class="display-4 fw-extrabold mb-3">Discover Curated Tech & Modern Essentials</h1>
                                <p class="lead mb-4 text-white-50">
                                    Handpicked high-performance gear, premium accessories, and lifestyle products engineered for modern everyday living.
                                </p>
                                <div class="d-flex flex-wrap gap-3 justify-content-center justify-content-lg-start">
                                    <a href="#product-catalog" class="btn btn-light btn-lg rounded-pill px-4 fw-semibold shadow">
                                        Shop Catalog <i class="bi bi-arrow-down-short"></i>
                                    </a>
                                    <a href="/category/electronics" class="btn btn-outline-light btn-lg rounded-pill px-4">Electronics</a>
                                </div>
                            </div>
                            <div class="col-lg-5 text-center d-none d-lg-block">
                                <div class="hero-image-wrapper p-3">
                                    <img src="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=700&q=80" alt="Featured" class="img-fluid rounded-4 shadow-lg hero-img">
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="hero-circle-1"></div>
                    <div class="hero-circle-2"></div>
                </section>"""

            # Build category pills
            pills_html = f"""<a href="/" class="btn btn-sm rounded-pill px-3 fw-medium {'btn-primary' if not category_slug else 'btn-outline-secondary'}">All Products</a>"""
            for c in categories:
                pills_html += f"""<a href="/category/{c['slug']}" class="btn btn-sm rounded-pill px-3 fw-medium {'btn-primary' if category_slug == c['slug'] else 'btn-outline-secondary'}"><i class="bi {c['icon']} me-1"></i>{c['name']}</a>"""

            # Product cards
            cards_html = ""
            if products:
                for p in products:
                    badge_markup = ""
                    if p['badge'] == 'HOT':
                        badge_markup = '<span class="badge bg-danger rounded-pill px-2 py-1 shadow-sm">🔥 HOT</span>'
                    elif p['badge'] == 'SALE':
                        badge_markup = '<span class="badge bg-success rounded-pill px-2 py-1 shadow-sm">SALE</span>'
                    elif p['badge'] == 'NEW':
                        badge_markup = '<span class="badge bg-primary rounded-pill px-2 py-1 shadow-sm">✨ NEW</span>'

                    orig_price_markup = f"""<span class="text-muted text-decoration-line-through small ms-1">${p['original_price']:.2f}</span>""" if p['original_price'] else ""

                    cards_html += f"""
                    <div class="col">
                        <div class="card h-100 product-card border-0 shadow-sm rounded-4 overflow-hidden position-relative">
                            <div class="product-badges position-absolute top-0 start-0 m-3 d-flex flex-column gap-1" style="z-index: 2;">
                                {badge_markup}
                            </div>
                            <div class="product-img-box bg-light overflow-hidden position-relative">
                                <a href="/product/{p['slug']}">
                                    <img src="{p['image_url']}" class="card-img-top product-img" alt="{p['name']}" loading="lazy">
                                </a>
                            </div>
                            <div class="card-body d-flex flex-column p-4">
                                <div class="d-flex align-items-center justify-content-between mb-2">
                                    <span class="text-muted small text-uppercase fw-semibold">{p['category_name']}</span>
                                    <div class="rating-stars small text-warning d-flex align-items-center gap-1">
                                        <i class="bi bi-star-fill"></i>
                                        <span class="text-dark fw-bold">{p['rating']}</span>
                                        <span class="text-muted">({p['reviews_count']})</span>
                                    </div>
                                </div>
                                <h5 class="card-title fw-bold fs-6 mb-2">
                                    <a href="/product/{p['slug']}" class="text-dark text-decoration-none product-title-link">
                                        {p['name']}
                                    </a>
                                </h5>
                                <p class="card-text text-secondary small flex-grow-1 mb-3">
                                    {p['description'][:85]}...
                                </p>
                                <div class="d-flex align-items-center justify-content-between mb-3">
                                    <div>
                                        <span class="fs-5 fw-bold text-dark">${p['price']:.2f}</span>
                                        {orig_price_markup}
                                    </div>
                                    <div>
                                        <span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill small">In Stock ({p['stock']})</span>
                                    </div>
                                </div>
                                <div class="d-grid gap-2">
                                    <button class="btn btn-primary rounded-pill fw-semibold add-to-cart-btn d-flex align-items-center justify-content-center gap-2"
                                            data-product-id="{p['id']}"
                                            data-product-name="{p['name']}"
                                            data-url="/cart/add/{p['id']}">
                                        <i class="bi bi-cart-plus"></i> Add to Cart
                                    </button>
                                    <a href="/product/{p['slug']}" class="btn btn-outline-light text-muted border-0 btn-sm rounded-pill">
                                        View Details <i class="bi bi-arrow-right"></i>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>"""
                products_grid_html = f"""<div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-3 row-cols-xl-4 g-4">{cards_html}</div>"""
            else:
                products_grid_html = """
                <div class="text-center py-5 my-5">
                    <div class="display-1 text-muted mb-3"><i class="bi bi-search"></i></div>
                    <h3 class="fw-bold">No Products Found</h3>
                    <p class="text-muted mb-4">We couldn't find any items matching your criteria.</p>
                    <a href="/" class="btn btn-primary rounded-pill px-4">Browse All Products</a>
                </div>"""

            page_header_html = ""
            if search_query:
                page_header_html = f"""
                <div class="d-flex align-items-center justify-content-between alert alert-light border rounded-3 p-3 mb-4">
                    <div>
                        <span class="text-muted">Search results for:</span> <strong>"{search_query}"</strong>
                        <span class="badge bg-secondary ms-2">{len(products)} items</span>
                    </div>
                    <a href="/" class="btn btn-sm btn-outline-danger rounded-pill">Clear Search</a>
                </div>"""
            elif active_cat:
                page_header_html = f"""
                <div class="mb-4">
                    <h2 class="fw-bold mb-1">{active_cat['name']}</h2>
                    <p class="text-muted small mb-0">{active_cat['description']}</p>
                </div>"""

            content = f"""
            {hero_html}
            <div class="container mb-5" id="product-catalog">
                <div class="d-flex align-items-center justify-content-between flex-wrap gap-3 mb-4 pb-2 border-bottom">
                    <div class="category-pills d-flex align-items-center gap-2 overflow-auto py-1">
                        {pills_html}
                    </div>
                    <div class="d-flex align-items-center gap-2 ms-auto">
                        <label class="small text-muted text-nowrap d-none d-sm-inline">Sort by:</label>
                        <select class="form-select form-select-sm rounded-pill border-secondary-subtle" onchange="location = this.value;">
                            <option value="?sort=newest" {'selected' if sort == 'newest' else ''}>Newest Arrivals</option>
                            <option value="?sort=price_asc" {'selected' if sort == 'price_asc' else ''}>Price: Low to High</option>
                            <option value="?sort=price_desc" {'selected' if sort == 'price_desc' else ''}>Price: High to Low</option>
                            <option value="?sort=rating" {'selected' if sort == 'rating' else ''}>Highest Rated</option>
                            <option value="?sort=popular" {'selected' if sort == 'popular' else ''}>Most Popular</option>
                        </select>
                    </div>
                </div>
                {page_header_html}
                {products_grid_html}
            </div>"""

            page_title = active_cat['name'] if active_cat else "Explore Products"
            self.send_html(self.render_layout(page_title, content, session))
            return

        # 2. Product Detail Page
        if path.startswith('/product/'):
            slug = path.split('/')[2]
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
            SELECT p.*, c.name as category_name, c.slug as category_slug, c.icon as category_icon
            FROM store_product p
            JOIN store_category c ON p.category_id = c.id
            WHERE p.slug = ?
            """, (slug,))
            p = cur.fetchone()

            if not p:
                conn.close()
                self.send_error(404, "Product not found")
                return
            p = dict(p)

            # Related products
            cur.execute("""
            SELECT * FROM store_product
            WHERE category_id = ? AND id != ?
            LIMIT 4
            """, (p['category_id'], p['id']))
            related = [dict(r) for r in cur.fetchall()]
            conn.close()

            orig_price_markup = f"""<span class="fs-5 text-muted text-decoration-line-through">${p['original_price']:.2f}</span>""" if p['original_price'] else ""

            related_html = ""
            for r in related:
                related_html += f"""
                <div class="col">
                    <div class="card h-100 border-0 shadow-sm rounded-4 overflow-hidden product-card">
                        <div class="product-img-box bg-light overflow-hidden">
                            <a href="/product/{r['slug']}">
                                <img src="{r['image_url']}" alt="{r['name']}" class="card-img-top product-img" loading="lazy">
                            </a>
                        </div>
                        <div class="card-body p-3 d-flex flex-column">
                            <h6 class="fw-bold mt-1 mb-2">
                                <a href="/product/{r['slug']}" class="text-dark text-decoration-none">{r['name']}</a>
                            </h6>
                            <div class="mt-auto d-flex align-items-center justify-content-between">
                                <span class="fw-bold text-primary">${r['price']:.2f}</span>
                                <a href="/product/{r['slug']}" class="btn btn-sm btn-outline-primary rounded-pill px-3">View</a>
                            </div>
                        </div>
                    </div>
                </div>"""

            content = f"""
            <div class="container py-4 mb-5">
                <nav aria-label="breadcrumb" class="mb-4">
                    <ol class="breadcrumb small">
                        <li class="breadcrumb-item"><a href="/" class="text-decoration-none">Home</a></li>
                        <li class="breadcrumb-item"><a href="/category/{p['category_slug']}" class="text-decoration-none">{p['category_name']}</a></li>
                        <li class="breadcrumb-item active">{p['name']}</li>
                    </ol>
                </nav>

                <div class="card border-0 shadow-sm rounded-4 overflow-hidden mb-5">
                    <div class="card-body p-4 p-lg-5">
                        <div class="row g-5 align-items-center">
                            <div class="col-lg-6">
                                <div class="product-gallery-box position-relative rounded-4 overflow-hidden bg-light text-center p-3">
                                    <img src="{p['image_url']}" alt="{p['name']}" class="img-fluid rounded-3 detail-product-img shadow-sm" style="max-height: 480px; object-fit: cover; width: 100%;">
                                </div>
                            </div>
                            <div class="col-lg-6">
                                <div class="d-flex align-items-center justify-content-between mb-2">
                                    <span class="badge bg-light text-primary border rounded-pill px-3 py-2 text-uppercase fw-semibold">
                                        <i class="bi {p['category_icon']} me-1"></i> {p['category_name']}
                                    </span>
                                    <span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill px-3 py-2">
                                        <i class="bi bi-check2-circle me-1"></i> In Stock ({p['stock']} units)
                                    </span>
                                </div>
                                <h1 class="fw-bold h2 mb-3">{p['name']}</h1>
                                <div class="d-flex align-items-center gap-2 mb-3">
                                    <div class="text-warning">
                                        <i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-half"></i>
                                    </div>
                                    <span class="fw-bold text-dark">{p['rating']}</span>
                                    <span class="text-muted small">({p['reviews_count']} verified reviews)</span>
                                </div>
                                <div class="d-flex align-items-baseline gap-3 mb-4">
                                    <span class="display-6 fw-extrabold text-primary">${p['price']:.2f}</span>
                                    {orig_price_markup}
                                </div>
                                <div class="mb-4">
                                    <h6 class="fw-bold text-uppercase text-secondary small">Product Overview</h6>
                                    <p class="text-muted leading-relaxed">{p['description']}</p>
                                </div>
                                <div class="row g-2 mb-4">
                                    <div class="col-6">
                                        <div class="d-flex align-items-center gap-2 text-secondary small bg-light p-2 rounded-3">
                                            <i class="bi bi-truck text-primary fs-5"></i><span>Free shipping over $50</span>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="d-flex align-items-center gap-2 text-secondary small bg-light p-2 rounded-3">
                                            <i class="bi bi-shield-check text-success fs-5"></i><span>1-Year Official Warranty</span>
                                        </div>
                                    </div>
                                </div>
                                <hr class="my-4">
                                <form action="/cart/add/{p['id']}" method="POST" id="detail-cart-form">
                                    <div class="d-flex flex-wrap align-items-center gap-3">
                                        <div class="quantity-input-group d-flex align-items-center border rounded-pill p-1 bg-light">
                                            <button type="button" class="btn btn-sm btn-light rounded-circle qty-btn" onclick="let el=document.getElementById('detail-quantity'); if(parseInt(el.value)>1) el.value=parseInt(el.value)-1;"><i class="bi bi-dash"></i></button>
                                            <input type="number" name="quantity" id="detail-quantity" value="1" min="1" max="{p['stock']}" class="form-control text-center border-0 bg-transparent fw-bold" style="width: 55px;" readonly>
                                            <button type="button" class="btn btn-sm btn-light rounded-circle qty-btn" onclick="let el=document.getElementById('detail-quantity'); if(parseInt(el.value)<{p['stock']}) el.value=parseInt(el.value)+1;"><i class="bi bi-plus"></i></button>
                                        </div>
                                        <button type="submit" class="btn btn-primary btn-lg rounded-pill px-4 fw-semibold flex-grow-1 d-flex align-items-center justify-content-center gap-2">
                                            <i class="bi bi-cart-plus"></i> Add to Cart
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="mt-5">
                    <h4 class="fw-bold mb-4">You May Also Like</h4>
                    <div class="row row-cols-1 row-cols-sm-2 row-cols-md-4 g-4">
                        {related_html}
                    </div>
                </div>
            </div>"""

            self.send_html(self.render_layout(p['name'], content, session))
            return

        # 3. Shopping Cart Page
        if path == '/cart':
            conn = get_db()
            cur = conn.cursor()
            if session.get('user_id'):
                cur.execute("""
                SELECT c.*, p.name, p.price, p.image_url, p.stock, cat.name as category_name
                FROM store_cartitem c
                JOIN store_product p ON c.product_id = p.id
                JOIN store_category cat ON p.category_id = cat.id
                WHERE c.user_id = ?
                """, (session['user_id'],))
            else:
                cur.execute("""
                SELECT c.*, p.name, p.price, p.image_url, p.stock, cat.name as category_name
                FROM store_cartitem c
                JOIN store_product p ON c.product_id = p.id
                JOIN store_category cat ON p.category_id = cat.id
                WHERE c.session_key = ?
                """, (self.session_id,))
            cart_items = [dict(r) for r in cur.fetchall()]
            conn.close()

            subtotal = sum(Decimal(str(item['price'])) * item['quantity'] for item in cart_items)
            shipping_fee = Decimal('0.00') if (subtotal == 0 or subtotal >= Decimal('50.00')) else Decimal('5.00')
            tax = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))
            total = subtotal + shipping_fee + tax

            if cart_items:
                items_rows = ""
                for item in cart_items:
                    line_total = Decimal(str(item['price'])) * item['quantity']
                    items_rows += f"""
                    <tr class="cart-item-row">
                        <td class="ps-4 py-3">
                            <div class="d-flex align-items-center gap-3">
                                <img src="{item['image_url']}" class="rounded-3 shadow-sm cart-item-thumb">
                                <div>
                                    <span class="badge bg-light text-secondary border small mb-1">{item['category_name']}</span>
                                    <h6 class="fw-bold mb-1">{item['name']}</h6>
                                    <span class="text-muted small">In stock: {item['stock']}</span>
                                </div>
                            </div>
                        </td>
                        <td class="text-center fw-medium py-3">${item['price']:.2f}</td>
                        <td class="text-center py-3">
                            <div class="d-inline-flex align-items-center border rounded-pill bg-light p-1">
                                <form action="/cart/update/{item['id']}" method="POST" class="d-inline">
                                    <input type="hidden" name="action" value="decrease">
                                    <button type="submit" class="btn btn-sm btn-link text-dark p-0 px-2"><i class="bi bi-dash"></i></button>
                                </form>
                                <span class="fw-bold px-2">{item['quantity']}</span>
                                <form action="/cart/update/{item['id']}" method="POST" class="d-inline">
                                    <input type="hidden" name="action" value="increase">
                                    <button type="submit" class="btn btn-sm btn-link text-dark p-0 px-2" {'disabled' if item['quantity']>=item['stock'] else ''}><i class="bi bi-plus"></i></button>
                                </form>
                            </div>
                        </td>
                        <td class="text-center fw-bold text-primary py-3">${line_total:.2f}</td>
                        <td class="pe-4 text-end py-3">
                            <form action="/cart/remove/{item['id']}" method="POST" class="d-inline">
                                <button type="submit" class="btn btn-sm btn-outline-danger rounded-circle p-2" title="Remove item">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </form>
                        </td>
                    </tr>"""

                shipping_badge = '<span class="badge bg-success-subtle text-success fw-bold">FREE</span>' if shipping_fee == 0 else f'<span class="fw-bold text-dark">${shipping_fee:.2f}</span>'

                content = f"""
                <div class="container py-4 mb-5">
                    <div class="d-flex align-items-center justify-content-between mb-4">
                        <div>
                            <h1 class="fw-bold h2 mb-1">Shopping Cart</h1>
                            <p class="text-muted small mb-0">Review your selected items before proceeding to checkout.</p>
                        </div>
                        <a href="/" class="btn btn-outline-secondary rounded-pill px-3 btn-sm">
                            <i class="bi bi-arrow-left me-1"></i> Continue Shopping
                        </a>
                    </div>

                    <div class="row g-4">
                        <div class="col-lg-8">
                            <div class="card border-0 shadow-sm rounded-4 overflow-hidden mb-4">
                                <div class="table-responsive">
                                    <table class="table align-middle mb-0 cart-table">
                                        <thead class="bg-light">
                                            <tr class="text-secondary small text-uppercase">
                                                <th scope="col" class="py-3 ps-4">Product</th>
                                                <th scope="col" class="py-3 text-center">Price</th>
                                                <th scope="col" class="py-3 text-center">Quantity</th>
                                                <th scope="col" class="py-3 text-center">Total</th>
                                                <th scope="col" class="py-3 pe-4 text-end">Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {items_rows}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div class="col-lg-4">
                            <div class="card border-0 shadow-sm rounded-4 p-4 sticky-top" style="top: 90px;">
                                <h5 class="fw-bold mb-3">Order Summary</h5>
                                <div class="d-flex justify-content-between mb-2">
                                    <span class="text-secondary">Subtotal</span>
                                    <span class="fw-bold text-dark">${subtotal:.2f}</span>
                                </div>
                                <div class="d-flex justify-content-between mb-2">
                                    <span class="text-secondary">Shipping Estimate</span>
                                    {shipping_badge}
                                </div>
                                <div class="d-flex justify-content-between mb-3">
                                    <span class="text-secondary">Estimated Tax (5%)</span>
                                    <span class="fw-bold text-dark">${tax:.2f}</span>
                                </div>
                                <hr class="my-3">
                                <div class="d-flex justify-content-between align-items-center mb-4">
                                    <span class="fs-5 fw-bold">Grand Total</span>
                                    <span class="fs-4 fw-extrabold text-primary">${total:.2f}</span>
                                </div>
                                <div class="d-grid gap-2">
                                    <a href="/checkout" class="btn btn-primary btn-lg rounded-pill fw-semibold shadow-sm d-flex align-items-center justify-content-center gap-2">
                                        Proceed to Checkout <i class="bi bi-arrow-right"></i>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>"""
            else:
                content = """
                <div class="container py-4 mb-5">
                    <div class="card border-0 shadow-sm rounded-4 p-5 text-center my-4">
                        <div class="py-5">
                            <div class="display-1 text-muted mb-3"><i class="bi bi-cart-x"></i></div>
                            <h3 class="fw-bold mb-2">Your Cart is Empty</h3>
                            <p class="text-muted mb-4">Looks like you haven't added any products to your shopping cart yet.</p>
                            <a href="/" class="btn btn-primary btn-lg rounded-pill px-4 fw-semibold">Explore Catalog & Shop Now</a>
                        </div>
                    </div>
                </div>"""

            self.send_html(self.render_layout("Shopping Cart", content, session))
            return

        # 4. Checkout Page
        if path == '/checkout':
            conn = get_db()
            cur = conn.cursor()
            if session.get('user_id'):
                cur.execute("""
                SELECT c.*, p.name, p.price, p.image_url
                FROM store_cartitem c
                JOIN store_product p ON c.product_id = p.id
                WHERE c.user_id = ?
                """, (session['user_id'],))
            else:
                cur.execute("""
                SELECT c.*, p.name, p.price, p.image_url
                FROM store_cartitem c
                JOIN store_product p ON c.product_id = p.id
                WHERE c.session_key = ?
                """, (self.session_id,))
            cart_items = [dict(r) for r in cur.fetchall()]
            conn.close()

            if not cart_items:
                session['messages'].append(('warning', "Your cart is empty! Add products first."))
                self.redirect('/')
                return

            subtotal = sum(Decimal(str(item['price'])) * item['quantity'] for item in cart_items)
            shipping_fee = Decimal('0.00') if subtotal >= Decimal('50.00') else Decimal('5.00')
            tax = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))
            total = subtotal + shipping_fee + tax

            items_mini = ""
            for item in cart_items:
                items_mini += f"""
                <div class="d-flex align-items-center justify-content-between py-2 border-bottom">
                    <div class="d-flex align-items-center gap-3">
                        <img src="{item['image_url']}" class="rounded-2" style="width: 50px; height: 50px; object-fit: cover;">
                        <div>
                            <h6 class="mb-0 fw-semibold small text-truncate" style="max-width: 180px;">{item['name']}</h6>
                            <span class="text-muted small">{item['quantity']} × ${item['price']:.2f}</span>
                        </div>
                    </div>
                    <span class="fw-bold text-dark small">${item['price']*item['quantity']:.2f}</span>
                </div>"""

            default_name = "Alex Morgan" if session.get('user_id') else ""
            default_email = "demo@store.com" if session.get('user_id') else ""

            content = f"""
            <div class="container py-4 mb-5">
                <div class="mb-4">
                    <h1 class="fw-bold h2 mb-1">Checkout & Order Processing</h1>
                    <p class="text-muted small mb-0">Please enter your shipping address and choose your preferred payment method.</p>
                </div>

                <form action="/checkout" method="POST">
                    <div class="row g-4">
                        <div class="col-lg-7">
                            <div class="card border-0 shadow-sm rounded-4 p-4 mb-4">
                                <h5 class="fw-bold mb-3"><span class="badge bg-primary rounded-circle p-2 small me-2">1</span>Customer Information</h5>
                                <div class="row g-3">
                                    <div class="col-12">
                                        <label class="form-label small fw-semibold">Full Name *</label>
                                        <input type="text" name="full_name" class="form-control" value="{default_name}" placeholder="John Doe" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-semibold">Email Address *</label>
                                        <input type="email" name="email" class="form-control" value="{default_email}" placeholder="john@example.com" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-semibold">Phone Number *</label>
                                        <input type="text" name="phone" class="form-control" value="+1 (555) 234-5678" required>
                                    </div>
                                </div>
                            </div>

                            <div class="card border-0 shadow-sm rounded-4 p-4 mb-4">
                                <h5 class="fw-bold mb-3"><span class="badge bg-primary rounded-circle p-2 small me-2">2</span>Shipping Address</h5>
                                <div class="row g-3">
                                    <div class="col-12">
                                        <label class="form-label small fw-semibold">Street Address *</label>
                                        <input type="text" name="address" class="form-control" value="742 Evergreen Terrace" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-semibold">City *</label>
                                        <input type="text" name="city" class="form-control" value="Springfield" required>
                                    </div>
                                    <div class="col-md-3">
                                        <label class="form-label small fw-semibold">State *</label>
                                        <input type="text" name="state" class="form-control" value="OR" required>
                                    </div>
                                    <div class="col-md-3">
                                        <label class="form-label small fw-semibold">ZIP Code *</label>
                                        <input type="text" name="postal_code" class="form-control" value="97477" required>
                                    </div>
                                </div>
                            </div>

                            <div class="card border-0 shadow-sm rounded-4 p-4">
                                <h5 class="fw-bold mb-3"><span class="badge bg-primary rounded-circle p-2 small me-2">3</span>Payment Method</h5>
                                <div class="mb-3">
                                    <select name="payment_method" class="form-select">
                                        <option value="Card">Credit / Debit Card (Simulated Sandbox)</option>
                                        <option value="COD">Cash on Delivery (COD)</option>
                                        <option value="UPI">UPI / Net Banking</option>
                                    </select>
                                </div>
                                <div class="alert alert-light border rounded-3 small text-muted d-flex align-items-center gap-2 mb-0">
                                    <i class="bi bi-info-circle text-primary fs-5"></i>
                                    <span>Safe sandbox checkout. No real money or card is billed.</span>
                                </div>
                            </div>
                        </div>

                        <div class="col-lg-5">
                            <div class="card border-0 shadow-sm rounded-4 p-4 sticky-top" style="top: 90px;">
                                <h5 class="fw-bold mb-3">Order Items ({len(cart_items)})</h5>
                                <div class="checkout-items-list mb-3 overflow-auto" style="max-height: 280px;">
                                    {items_mini}
                                </div>
                                <div class="d-flex justify-content-between mb-2 small">
                                    <span class="text-secondary">Subtotal</span>
                                    <span class="fw-bold text-dark">${subtotal:.2f}</span>
                                </div>
                                <div class="d-flex justify-content-between mb-2 small">
                                    <span class="text-secondary">Shipping</span>
                                    <span class="fw-bold text-dark">${shipping_fee:.2f}</span>
                                </div>
                                <div class="d-flex justify-content-between mb-3 small">
                                    <span class="text-secondary">Estimated Tax (5%)</span>
                                    <span class="fw-bold text-dark">${tax:.2f}</span>
                                </div>
                                <hr class="my-3">
                                <div class="d-flex justify-content-between align-items-center mb-4">
                                    <span class="fs-5 fw-bold">Total Due</span>
                                    <span class="fs-4 fw-extrabold text-primary">${total:.2f}</span>
                                </div>
                                <button type="submit" class="btn btn-primary btn-lg rounded-pill fw-semibold shadow-sm w-100 d-flex align-items-center justify-content-center gap-2">
                                    <i class="bi bi-bag-check-fill"></i> Place Order Now
                                </button>
                            </div>
                        </div>
                    </div>
                </form>
            </div>"""

            self.send_html(self.render_layout("Checkout", content, session))
            return

        # 5. Order Success Page
        if path.startswith('/order/success/'):
            order_num = path.split('/')[3]
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM store_order WHERE order_number = ?", (order_num,))
            order = cur.fetchone()
            if not order:
                conn.close()
                self.send_error(404, "Order not found")
                return
            order = dict(order)

            cur.execute("SELECT * FROM store_orderitem WHERE order_id = ?", (order['id'],))
            items = [dict(r) for r in cur.fetchall()]
            conn.close()

            items_rows = ""
            for it in items:
                sub = it['price'] * it['quantity']
                items_rows += f"""
                <tr>
                    <td class="py-3"><span class="fw-semibold text-dark">{it['product_name']}</span></td>
                    <td class="text-center py-3">{it['quantity']}</td>
                    <td class="text-end py-3">${it['price']:.2f}</td>
                    <td class="text-end fw-bold py-3">${sub:.2f}</td>
                </tr>"""

            content = f"""
            <div class="container py-5 mb-5">
                <div class="row justify-content-center">
                    <div class="col-lg-8">
                        <div class="card border-0 shadow-sm rounded-4 overflow-hidden mb-4 text-center p-4 p-md-5">
                            <div class="mb-3">
                                <div class="d-inline-flex align-items-center justify-content-center bg-success-subtle text-success rounded-circle" style="width: 80px; height: 80px;">
                                    <i class="bi bi-check-circle-fill display-5"></i>
                                </div>
                            </div>
                            <h1 class="fw-extrabold h2 mb-2">Thank You For Your Order!</h1>
                            <p class="text-muted mb-3">Your order has been placed successfully and is currently being processed.</p>
                            <div class="d-flex flex-wrap justify-content-center gap-3">
                                <span class="badge bg-light text-dark border rounded-pill px-3 py-2 fs-6">Order Number: <strong>#{order['order_number']}</strong></span>
                                <span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill px-3 py-2 fs-6">Status: <strong>{order['status']}</strong></span>
                            </div>
                        </div>

                        <div class="card border-0 shadow-sm rounded-4 overflow-hidden mb-4 p-4 p-md-5">
                            <div class="d-flex align-items-center justify-content-between mb-4 border-bottom pb-3">
                                <h5 class="fw-bold mb-0">Order Receipt & Breakdown</h5>
                                <span class="text-muted small">{order['created_at']}</span>
                            </div>
                            <div class="row g-3 mb-4 bg-light rounded-3 p-3">
                                <div class="col-md-6">
                                    <h6 class="text-uppercase text-secondary small fw-bold mb-2">Customer Info</h6>
                                    <p class="mb-1 fw-semibold text-dark">{order['full_name']}</p>
                                    <p class="mb-1 text-muted small"><i class="bi bi-envelope me-1"></i>{order['email']}</p>
                                    <p class="mb-0 text-muted small"><i class="bi bi-telephone me-1"></i>{order['phone']}</p>
                                </div>
                                <div class="col-md-6">
                                    <h6 class="text-uppercase text-secondary small fw-bold mb-2">Shipping Destination</h6>
                                    <p class="mb-1 text-dark">{order['address']}</p>
                                    <p class="mb-1 text-muted small">{order['city']}, {order['state']} {order['postal_code']}</p>
                                    <p class="mb-0 text-muted small">{order['country']}</p>
                                </div>
                            </div>

                            <div class="table-responsive mb-4">
                                <table class="table align-middle">
                                    <thead class="bg-light">
                                        <tr class="text-secondary small text-uppercase">
                                            <th scope="col" class="py-2">Item</th>
                                            <th scope="col" class="py-2 text-center">Qty</th>
                                            <th scope="col" class="py-2 text-end">Price</th>
                                            <th scope="col" class="py-2 text-end">Subtotal</th>
                                        </tr>
                                    </thead>
                                    <tbody>{items_rows}</tbody>
                                </table>
                            </div>

                            <div class="row justify-content-end">
                                <div class="col-md-6">
                                    <div class="d-flex justify-content-between mb-2 small">
                                        <span class="text-secondary">Shipping:</span>
                                        <span class="fw-semibold">${order['shipping_fee']:.2f}</span>
                                    </div>
                                    <div class="d-flex justify-content-between mb-2 small">
                                        <span class="text-secondary">Payment Method:</span>
                                        <span class="fw-semibold">{order['payment_method']}</span>
                                    </div>
                                    <hr>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="fw-bold fs-5">Total Paid:</span>
                                        <span class="fw-extrabold fs-4 text-primary">${order['total_amount']:.2f}</span>
                                    </div>
                                </div>
                            </div>

                            <div class="d-flex flex-wrap gap-3 justify-content-between align-items-center mt-5 pt-3 border-top">
                                <a href="/" class="btn btn-outline-secondary rounded-pill px-4"><i class="bi bi-arrow-left me-1"></i> Continue Shopping</a>
                                <button type="button" class="btn btn-light border rounded-pill px-4" onclick="window.print()"><i class="bi bi-printer me-1"></i> Print Invoice</button>
                                <a href="/orders" class="btn btn-primary rounded-pill px-4">View Orders</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>"""

            self.send_html(self.render_layout(f"Order #{order['order_number']}", content, session))
            return

        # 6. Orders History Page
        if path == '/orders':
            if not session.get('user_id'):
                session['messages'].append(('info', "Please sign in to view your orders."))
                self.redirect('/login')
                return

            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM store_order WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
            orders = [dict(r) for r in cur.fetchall()]

            orders_cards = ""
            for ord in orders:
                cur.execute("""
                SELECT i.*, p.image_url
                FROM store_orderitem i
                LEFT JOIN store_product p ON i.product_id = p.id
                WHERE i.order_id = ?
                """, (ord['id'],))
                items = [dict(r) for r in cur.fetchall()]

                items_html = ""
                for it in items:
                    img = it['image_url'] if it['image_url'] else 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=100'
                    items_html += f"""
                    <div class="col-md-6 col-lg-4">
                        <div class="d-flex align-items-center gap-3 p-2 rounded-3 bg-light border">
                            <img src="{img}" class="rounded-2" style="width: 55px; height: 55px; object-fit: cover;">
                            <div class="overflow-hidden">
                                <h6 class="mb-0 fw-bold small text-truncate">{it['product_name']}</h6>
                                <span class="text-muted small">Qty: {it['quantity']} × ${it['price']:.2f}</span>
                            </div>
                        </div>
                    </div>"""

                orders_cards += f"""
                <div class="card border-0 shadow-sm rounded-4 overflow-hidden mb-4">
                    <div class="card-header bg-light border-0 py-3 px-4 d-flex flex-wrap align-items-center justify-content-between gap-3">
                        <div class="d-flex align-items-center gap-3">
                            <div>
                                <span class="text-muted small text-uppercase fw-semibold d-block">Order Placed</span>
                                <span class="fw-bold small">{ord['created_at'][:10]}</span>
                            </div>
                            <div class="vr mx-2"></div>
                            <div>
                                <span class="text-muted small text-uppercase fw-semibold d-block">Total</span>
                                <span class="fw-bold small text-primary">${ord['total_amount']:.2f}</span>
                            </div>
                            <div class="vr mx-2"></div>
                            <div>
                                <span class="text-muted small text-uppercase fw-semibold d-block">Ship To</span>
                                <span class="fw-bold small">{ord['full_name']}</span>
                            </div>
                        </div>
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill px-3 py-2">{ord['status']}</span>
                            <span class="text-muted small">#{ord['order_number']}</span>
                        </div>
                    </div>
                    <div class="card-body p-4">
                        <div class="row g-3">{items_html}</div>
                        <div class="d-flex justify-content-end align-items-center gap-2 mt-3 pt-3 border-top">
                            <a href="/order/success/{ord['order_number']}" class="btn btn-sm btn-outline-secondary rounded-pill px-3">View Receipt</a>
                        </div>
                    </div>
                </div>"""

            conn.close()

            if not orders_cards:
                orders_cards = """
                <div class="card border-0 shadow-sm rounded-4 p-5 text-center my-4">
                    <div class="py-5">
                        <div class="display-1 text-muted mb-3"><i class="bi bi-box-seam"></i></div>
                        <h3 class="fw-bold mb-2">No Orders Placed Yet</h3>
                        <p class="text-muted mb-4">When you place orders, they will appear here with full receipts.</p>
                        <a href="/" class="btn btn-primary rounded-pill px-4">Start Shopping</a>
                    </div>
                </div>"""

            content = f"""
            <div class="container py-4 mb-5">
                <div class="d-flex align-items-center justify-content-between mb-4">
                    <div>
                        <h1 class="fw-bold h2 mb-1">My Orders</h1>
                        <p class="text-muted small mb-0">Track and review your previous purchases.</p>
                    </div>
                    <a href="/" class="btn btn-outline-primary rounded-pill btn-sm px-3"><i class="bi bi-cart-plus me-1"></i> Browse Store</a>
                </div>
                {orders_cards}
            </div>"""

            self.send_html(self.render_layout("My Orders", content, session))
            return

        # 7. Login Page
        if path == '/login':
            content = """
            <div class="container py-5 mb-5">
                <div class="row justify-content-center">
                    <div class="col-md-6 col-lg-5">
                        <div class="card border-0 shadow-sm rounded-4 p-4 p-md-5">
                            <div class="text-center mb-4">
                                <div class="brand-icon mx-auto mb-3" style="width: 50px; height: 50px; font-size: 1.5rem;"><i class="bi bi-lock-fill"></i></div>
                                <h2 class="fw-bold h3 mb-1">Welcome Back</h2>
                                <p class="text-muted small">Log in to manage your cart, orders, and saved addresses.</p>
                            </div>
                            <form method="POST" action="/login">
                                <div class="mb-3">
                                    <label class="form-label small fw-semibold">Username</label>
                                    <div class="input-group">
                                        <span class="input-group-text bg-light border-end-0"><i class="bi bi-person text-muted"></i></span>
                                        <input type="text" name="username" class="form-control bg-light border-start-0 ps-0" placeholder="Enter username" required autofocus>
                                    </div>
                                </div>
                                <div class="mb-4">
                                    <label class="form-label small fw-semibold">Password</label>
                                    <div class="input-group">
                                        <span class="input-group-text bg-light border-end-0"><i class="bi bi-key text-muted"></i></span>
                                        <input type="password" name="password" class="form-control bg-light border-start-0 ps-0" placeholder="••••••••" required>
                                    </div>
                                </div>
                                <button type="submit" class="btn btn-primary btn-lg rounded-pill w-100 fw-semibold mb-3 shadow-sm">Sign In</button>
                                <div class="alert alert-info py-2 px-3 small rounded-3 mb-4 text-center">
                                    <span class="d-block fw-semibold mb-1">Demo Credentials:</span>
                                    <code>demouser</code> / <code>demo12345</code><br>
                                    Admin: <code>admin</code> / <code>admin12345</code>
                                </div>
                                <div class="text-center small text-muted">
                                    Don't have an account yet? <a href="/register" class="fw-bold text-primary text-decoration-none">Create account</a>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>"""
            self.send_html(self.render_layout("Sign In", content, session))
            return

        # 8. Register Page
        if path == '/register':
            content = """
            <div class="container py-5 mb-5">
                <div class="row justify-content-center">
                    <div class="col-md-7 col-lg-6">
                        <div class="card border-0 shadow-sm rounded-4 p-4 p-md-5">
                            <div class="text-center mb-4">
                                <div class="brand-icon mx-auto mb-3" style="width: 50px; height: 50px; font-size: 1.5rem;"><i class="bi bi-person-plus-fill"></i></div>
                                <h2 class="fw-bold h3 mb-1">Create an Account</h2>
                                <p class="text-muted small">Join NovaStore today for faster checkout, order tracking, and exclusive discounts.</p>
                            </div>
                            <form method="POST" action="/register">
                                <div class="row g-3 mb-3">
                                    <div class="col-md-6">
                                        <label class="form-label small fw-semibold">First Name</label>
                                        <input type="text" name="first_name" class="form-control" placeholder="First Name" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label small fw-semibold">Last Name</label>
                                        <input type="text" name="last_name" class="form-control" placeholder="Last Name" required>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small fw-semibold">Username *</label>
                                    <input type="text" name="username" class="form-control" placeholder="Choose a username" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small fw-semibold">Email Address *</label>
                                    <input type="email" name="email" class="form-control" placeholder="your.email@example.com" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small fw-semibold">Password *</label>
                                    <input type="password" name="password" class="form-control" placeholder="Create password (min 6 chars)" minlength="6" required>
                                </div>
                                <button type="submit" class="btn btn-primary btn-lg rounded-pill w-100 fw-semibold mb-3 shadow-sm">Register Account</button>
                                <div class="text-center small text-muted">
                                    Already have an account? <a href="/login" class="fw-bold text-primary text-decoration-none">Log In</a>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>"""
            self.send_html(self.render_layout("Register", content, session))
            return

        # 9. Logout
        if path == '/logout':
            session['user_id'] = None
            session['username'] = None
            session['messages'].append(('info', "You have been logged out."))
            self.redirect('/')
            return

        self.send_error(404, "Page Not Found")

    def do_POST(self):
        session = self.get_session()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Read POST body
        content_len = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_len).decode('utf-8')
        post_params = urllib.parse.parse_qs(post_data)

        # 1. Add to cart
        if path.startswith('/cart/add/'):
            product_id = int(path.split('/')[3])
            qty = int(post_params.get('quantity', ['1'])[0])
            if qty < 1: qty = 1

            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT name, stock FROM store_product WHERE id = ?", (product_id,))
            prod = cur.fetchone()
            if not prod:
                conn.close()
                self.send_error(404, "Product not found")
                return

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if session.get('user_id'):
                cur.execute("SELECT id, quantity FROM store_cartitem WHERE user_id = ? AND product_id = ?",
                            (session['user_id'], product_id))
                row = cur.fetchone()
                if row:
                    cur.execute("UPDATE store_cartitem SET quantity = quantity + ?, updated_at = ? WHERE id = ?",
                                (qty, now, row['id']))
                else:
                    cur.execute("INSERT INTO store_cartitem (quantity, created_at, updated_at, product_id, user_id) VALUES (?, ?, ?, ?, ?)",
                                (qty, now, now, product_id, session['user_id']))
            else:
                cur.execute("SELECT id, quantity FROM store_cartitem WHERE session_key = ? AND product_id = ?",
                            (self.session_id, product_id))
                row = cur.fetchone()
                if row:
                    cur.execute("UPDATE store_cartitem SET quantity = quantity + ?, updated_at = ? WHERE id = ?",
                                (qty, now, row['id']))
                else:
                    cur.execute("INSERT INTO store_cartitem (session_key, quantity, created_at, updated_at, product_id) VALUES (?, ?, ?, ?, ?)",
                                (self.session_id, qty, now, now, product_id))

            conn.commit()
            cart_count = self.get_cart_count(session)
            conn.close()

            is_ajax = (self.headers.get('X-Requested-With') == 'XMLHttpRequest')
            if is_ajax:
                self.send_json({
                    'success': True,
                    'message': f'"{prod[0]}" added to cart!',
                    'cart_count': cart_count,
                    'product_name': prod[0]
                })
            else:
                session['messages'].append(('success', f'Added "{prod[0]}" to your shopping cart.'))
                self.redirect('/cart')
            return

        # 2. Update cart item
        if path.startswith('/cart/update/'):
            item_id = int(path.split('/')[3])
            action = post_params.get('action', [''])[0]

            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT quantity FROM store_cartitem WHERE id = ?", (item_id,))
            row = cur.fetchone()
            if row:
                current_qty = row['quantity']
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if action == 'increase':
                    cur.execute("UPDATE store_cartitem SET quantity = quantity + 1, updated_at = ? WHERE id = ?", (now, item_id))
                elif action == 'decrease':
                    if current_qty > 1:
                        cur.execute("UPDATE store_cartitem SET quantity = quantity - 1, updated_at = ? WHERE id = ?", (now, item_id))
                    else:
                        cur.execute("DELETE FROM store_cartitem WHERE id = ?", (item_id,))
                conn.commit()
            conn.close()
            self.redirect('/cart')
            return

        # 3. Remove from cart
        if path.startswith('/cart/remove/'):
            item_id = int(path.split('/')[3])
            conn = get_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM store_cartitem WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            session['messages'].append(('info', "Item removed from cart."))
            self.redirect('/cart')
            return

        # 4. Checkout Place Order
        if path == '/checkout':
            full_name = post_params.get('full_name', [''])[0].strip()
            email = post_params.get('email', [''])[0].strip()
            phone = post_params.get('phone', [''])[0].strip()
            address = post_params.get('address', [''])[0].strip()
            city = post_params.get('city', [''])[0].strip()
            state = post_params.get('state', [''])[0].strip()
            postal_code = post_params.get('postal_code', [''])[0].strip()
            payment_method = post_params.get('payment_method', ['Card'])[0]

            conn = get_db()
            cur = conn.cursor()
            if session.get('user_id'):
                cur.execute("""
                SELECT c.*, p.name, p.price, p.stock
                FROM store_cartitem c
                JOIN store_product p ON c.product_id = p.id
                WHERE c.user_id = ?
                """, (session['user_id'],))
            else:
                cur.execute("""
                SELECT c.*, p.name, p.price, p.stock
                FROM store_cartitem c
                JOIN store_product p ON c.product_id = p.id
                WHERE c.session_key = ?
                """, (self.session_id,))
            cart_items = [dict(r) for r in cur.fetchall()]

            if not cart_items:
                conn.close()
                self.redirect('/')
                return

            subtotal = sum(Decimal(str(item['price'])) * item['quantity'] for item in cart_items)
            shipping_fee = Decimal('0.00') if subtotal >= Decimal('50.00') else Decimal('5.00')
            tax = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))
            total = subtotal + shipping_fee + tax
            order_number = "ORD-" + uuid.uuid4().hex[:8].upper()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cur.execute("""
            INSERT INTO store_order (
                order_number, full_name, email, phone, address, city, state, postal_code,
                country, payment_method, shipping_fee, total_amount, status, notes,
                created_at, updated_at, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'United States', ?, ?, ?, 'Processing', '', ?, ?, ?)
            """, (order_number, full_name, email, phone, address, city, state, postal_code,
                  payment_method, float(shipping_fee), float(total), now, now, session.get('user_id')))

            order_id = cur.lastrowid

            for item in cart_items:
                cur.execute("""
                INSERT INTO store_orderitem (product_name, price, quantity, order_id, product_id)
                VALUES (?, ?, ?, ?, ?)
                """, (item['name'], float(item['price']), item['quantity'], order_id, item['product_id']))

                # Update stock
                cur.execute("UPDATE store_product SET stock = MAX(0, stock - ?) WHERE id = ?", (item['quantity'], item['product_id']))

            # Clear cart
            if session.get('user_id'):
                cur.execute("DELETE FROM store_cartitem WHERE user_id = ?", (session['user_id'],))
            else:
                cur.execute("DELETE FROM store_cartitem WHERE session_key = ?", (self.session_id,))

            conn.commit()
            conn.close()

            session['messages'].append(('success', f"Order #{order_number} placed successfully!"))
            self.redirect(f"/order/success/{order_number}")
            return

        # 5. User Login POST
        if path == '/login':
            username = post_params.get('username', [''])[0].strip()
            password = post_params.get('password', [''])[0].strip()

            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id, password FROM auth_user WHERE username = ?", (username,))
            user = cur.fetchone()

            # For demo purposes, check against demo/admin or created hash
            valid = False
            if user:
                # Accept if matches demo accounts or hashed
                if (username == 'demouser' and password == 'demo12345') or (username == 'admin' and password == 'admin12345'):
                    valid = True
                elif user['password'].startswith('pbkdf2_'):
                    import hashlib
                    salt = "codealphasalt"
                    h = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
                    expected = f"pbkdf2_sha256$100000${salt}${h.hex()}"
                    if user['password'] == expected:
                        valid = True

            if valid:
                session['user_id'] = user['id']
                session['username'] = username
                # Transfer guest cart items to user
                cur.execute("UPDATE store_cartitem SET user_id = ?, session_key = NULL WHERE session_key = ?",
                            (user['id'], self.session_id))
                conn.commit()
                conn.close()
                session['messages'].append(('success', f"Welcome back, {username}!"))
                self.redirect('/')
                return
            else:
                conn.close()
                session['messages'].append(('danger', "Invalid username or password. Please try again."))
                self.redirect('/login')
                return

        # 6. User Registration POST
        if path == '/register':
            username = post_params.get('username', [''])[0].strip()
            email = post_params.get('email', [''])[0].strip()
            password = post_params.get('password', [''])[0].strip()
            first_name = post_params.get('first_name', [''])[0].strip()
            last_name = post_params.get('last_name', [''])[0].strip()

            if not username or not password or len(password) < 6:
                session['messages'].append(('danger', "Please enter a valid username and password (min 6 characters)."))
                self.redirect('/register')
                return

            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id FROM auth_user WHERE username = ? OR email = ?", (username, email))
            if cur.fetchone():
                conn.close()
                session['messages'].append(('danger', "Username or email is already registered."))
                self.redirect('/register')
                return

            import hashlib
            salt = "codealphasalt"
            h = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            hashed_pwd = f"pbkdf2_sha256$100000${salt}${h.hex()}"
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cur.execute("""
            INSERT INTO auth_user (
                password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined
            ) VALUES (?, 0, ?, ?, ?, ?, 0, 1, ?)
            """, (hashed_pwd, username, first_name, last_name, email, now))
            new_user_id = cur.lastrowid

            # Transfer guest cart
            cur.execute("UPDATE store_cartitem SET user_id = ?, session_key = NULL WHERE session_key = ?",
                        (new_user_id, self.session_id))
            conn.commit()
            conn.close()

            session['user_id'] = new_user_id
            session['username'] = username
            session['messages'].append(('success', f"Account registered successfully! Welcome, {username}."))
            self.redirect('/')
            return

        self.send_error(404, "Unknown endpoint")

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), NovaStoreHandler) as httpd:
        print(f"================================================================")
        print(f"🚀 NovaStore Server is live at: http://localhost:{PORT}")
        print(f"👉 Press Ctrl+C in your terminal to stop the server.")
        print(f"================================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == '__main__':
    run_server()
