"""
routes/admin_routes.py
Admin-only dashboard for products, orders, users, subscriptions & stats.
All routes are prefixed with /admin via Blueprint url_prefix.
"""

import logging
import os
import uuid
from functools import wraps
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from werkzeug.utils import secure_filename
from services.product_service import (get_all_products, get_product_by_id,
                                      add_product, update_product, delete_product,
                                      update_stock)
from services.order_service import get_all_orders, update_order_status, get_sales_stats
from services.user_service import get_all_users
from services.subscription_service import (get_all_subscriptions,
                                           update_subscription_status)
import config.settings as settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_image(file):
    """Save an uploaded image to static/uploads and return its URL path."""
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, unique_name))
    return url_for('static', filename=f'uploads/{unique_name}')
admin_bp = Blueprint('admin', __name__)


# ── Guards ─────────────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('product.home'))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ──────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@admin_required
def dashboard():
    stats    = get_sales_stats()
    products = get_all_products()
    return render_template('admin/dashboard.html',
                           stats=stats,
                           total_products=len(products),
                           total_users=len(get_all_users()),
                           categories=settings.CATEGORIES)


# ── Product Management ─────────────────────────────────────────────────────────

@admin_bp.route('/products')
@admin_required
def manage_products():
    products = get_all_products()
    return render_template('admin/products.html',
                           products=products,
                           categories=settings.CATEGORIES)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product_view():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price       = float(request.form.get('price', 0))
        category    = request.form.get('category', '')
        stock       = int(request.form.get('stock', 0))
        weight      = request.form.get('weight', '').strip()

        # Handle image: uploaded file takes priority over URL
        image_url = ''
        uploaded_file = request.files.get('image_file')
        if uploaded_file and uploaded_file.filename:
            saved = save_uploaded_image(uploaded_file)
            if saved:
                image_url = saved
            else:
                flash('Invalid image format. Use PNG, JPG, JPEG, GIF or WEBP.', 'danger')
                return render_template('admin/add_product.html', categories=settings.CATEGORIES)
        else:
            image_url = request.form.get('image_url', '').strip()

        if not all([name, description, price, category]):
            flash('Name, description, price and category are required.', 'danger')
            return render_template('admin/add_product.html',
                                   categories=settings.CATEGORIES)

        result = add_product(name, description, price, category,
                             stock, image_url, weight)
        if result['success']:
            flash(f'Product "{name}" added successfully!', 'success')
            return redirect(url_for('admin.manage_products'))
        else:
            flash(result['error'], 'danger')

    return render_template('admin/add_product.html', categories=settings.CATEGORIES)


@admin_bp.route('/products/<product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin.manage_products'))

    if request.method == 'POST':
        # Handle image: uploaded file takes priority over URL
        uploaded_file = request.files.get('image_file')
        if uploaded_file and uploaded_file.filename:
            saved = save_uploaded_image(uploaded_file)
            if saved:
                image_url = saved
            else:
                flash('Invalid image format. Use PNG, JPG, JPEG, GIF or WEBP.', 'danger')
                return render_template('admin/edit_product.html', product=product,
                                       categories=settings.CATEGORIES)
        else:
            image_url = request.form.get('image_url', product.get('image_url', '')).strip()

        # Safe conversions — fall back to current product value if field is blank
        raw_price = request.form.get('price', '').strip()
        raw_stock = request.form.get('stock', '').strip()

        fields = {
            'name':        request.form.get('name', '').strip(),
            'description': request.form.get('description', '').strip(),
            'price':       float(raw_price) if raw_price else float(product.get('price', 0)),
            'category':    request.form.get('category', product.get('category', '')),
            'stock':       int(raw_stock)   if raw_stock  else int(product.get('stock', 0)),
            'weight':      request.form.get('weight', '').strip(),
            'image_url':   image_url,
            'is_active':   request.form.get('is_active') == 'on',
        }
        if update_product(product_id, fields):
            flash('Product updated.', 'success')
            return redirect(url_for('admin.manage_products'))
        else:
            flash('Update failed.', 'danger')

    return render_template('admin/edit_product.html',
                           product=product,
                           categories=settings.CATEGORIES)


@admin_bp.route('/products/<product_id>/delete', methods=['POST'])
@admin_required
def delete_product_view(product_id):
    delete_product(product_id)
    flash('Product deactivated.', 'info')
    return redirect(url_for('admin.manage_products'))


@admin_bp.route('/products/<product_id>/stock', methods=['POST'])
@admin_required
def update_stock_view(product_id):
    delta = int(request.form.get('delta', 0))
    try:
        update_stock(product_id, delta)
        flash(f'Stock updated by {delta:+d}.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.manage_products'))


# ── Order Management ───────────────────────────────────────────────────────────

@admin_bp.route('/orders')
@admin_required
def manage_orders():
    orders = get_all_orders()
    return render_template('admin/orders.html', orders=orders)


@admin_bp.route('/orders/<order_id>/status', methods=['POST'])
@admin_required
def update_order(order_id):
    status = request.form.get('status')
    if update_order_status(order_id, status):
        flash(f'Order status updated to "{status}".', 'success')
    else:
        flash('Invalid status.', 'danger')
    return redirect(url_for('admin.manage_orders'))


# ── User Management ────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@admin_required
def manage_users():
    users = get_all_users()
    return render_template('admin/users.html', users=users)


# ── Subscription Management ────────────────────────────────────────────────────

@admin_bp.route('/subscriptions')
@admin_required
def manage_subscriptions():
    subs = get_all_subscriptions()
    return render_template('admin/subscriptions.html', subscriptions=subs)


@admin_bp.route('/subscriptions/<sub_id>/status', methods=['POST'])
@admin_required
def update_sub_status(sub_id):
    status = request.form.get('status')
    if update_subscription_status(sub_id, status):
        flash(f'Subscription status updated to "{status}".', 'success')
    else:
        flash('Invalid status.', 'danger')
    return redirect(url_for('admin.manage_subscriptions'))
