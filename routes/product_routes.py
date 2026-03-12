"""
routes/product_routes.py
Home page, product browsing, search, and product detail.
"""

import logging
from flask import (Blueprint, render_template, request,
                   redirect, url_for, session, flash)
from services.product_service import (get_all_products, get_product_by_id,
                                      get_featured_products, get_recommendations)
from services.order_service import get_orders_by_user
import config.settings as settings

logger = logging.getLogger(__name__)
product_bp = Blueprint('product', __name__)


@product_bp.route('/')
def home():
    featured  = get_featured_products(6)
    categories = settings.CATEGORIES

    # Personalized recommendations if logged in
    recommendations = []
    if 'user_id' in session:
        orders = get_orders_by_user(session['user_id'])
        recommendations = get_recommendations(orders, limit=4)

    return render_template(
        'product/home.html',
        featured=featured,
        categories=categories,
        recommendations=recommendations,
    )


@product_bp.route('/products')
def product_list():
    category = request.args.get('category', '')
    query    = request.args.get('q', '').lower()

    products = get_all_products(category if category else None)
    products = [p for p in products if p.get('is_active', True)]

    if query:
        products = [p for p in products
                    if query in p.get('name', '').lower()
                    or query in p.get('description', '').lower()]

    categories = settings.CATEGORIES
    return render_template(
        'product/product_list.html',
        products=products,
        categories=categories,
        selected_category=category,
        search_query=request.args.get('q', ''),
    )


@product_bp.route('/products/<product_id>')
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product or not product.get('is_active', True):
        flash('Product not found.', 'warning')
        return redirect(url_for('product.product_list'))

    # Related products from same category
    all_in_cat = get_all_products(product.get('category'))
    related = [p for p in all_in_cat
               if p['product_id'] != product_id and p.get('is_active', True)][:4]

    return render_template(
        'product/product_detail.html',
        product=product,
        related=related,
    )
