"""
routes/cart_routes.py
Session-based shopping cart management (add, update, remove, view).
"""

import logging
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from services.product_service import get_product_by_id

logger = logging.getLogger(__name__)
cart_bp = Blueprint('cart', __name__)


def _get_cart() -> list:
    """Return the current cart list from the session."""
    return session.get('cart', [])


def _save_cart(cart: list):
    """Persist the cart list back to session."""
    session['cart'] = cart
    session.modified = True


def _cart_total(cart: list) -> float:
    return sum(item['price'] * item['quantity'] for item in cart)


@cart_bp.route('/cart')
def view_cart():
    cart  = _get_cart()
    total = _cart_total(cart)
    return render_template('cart/cart.html', cart=cart, total=total)


@cart_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        flash('Please log in to add items to cart.', 'warning')
        return redirect(url_for('auth.login', next=request.referrer))

    product_id = request.form.get('product_id')
    quantity   = int(request.form.get('quantity', 1))

    if quantity < 1:
        flash('Invalid quantity.', 'danger')
        return redirect(request.referrer or url_for('product.product_list'))

    product = get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(request.referrer or url_for('product.product_list'))

    stock = int(product.get('stock', 0))
    if stock < quantity:
        flash(f"Only {stock} unit(s) available.", 'warning')
        return redirect(request.referrer or url_for('product.product_list'))

    cart = _get_cart()
    # Check if already in cart
    for item in cart:
        if item['product_id'] == product_id:
            new_qty = item['quantity'] + quantity
            if new_qty > stock:
                flash(f"Cannot add more — only {stock} unit(s) in stock.", 'warning')
                return redirect(request.referrer or url_for('product.product_list'))
            item['quantity'] = new_qty
            _save_cart(cart)
            flash(f"Updated quantity for {product['name']}.", 'success')
            return redirect(url_for('cart.view_cart'))

    cart.append({
        'product_id':   product_id,
        'name':         product['name'],
        'price':        float(product['price']),
        'quantity':     quantity,
        'image_url':    product.get('image_url', ''),
        'category':     product.get('category', ''),
    })
    _save_cart(cart)
    flash(f"{product['name']} added to cart! 🛒", 'success')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/cart/update', methods=['POST'])
def update_cart():
    product_id = request.form.get('product_id')
    quantity   = int(request.form.get('quantity', 1))
    cart = _get_cart()

    if quantity < 1:
        # Remove item
        cart = [i for i in cart if i['product_id'] != product_id]
        flash('Item removed from cart.', 'info')
    else:
        product = get_product_by_id(product_id)
        stock   = int(product.get('stock', 0)) if product else 0
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] = min(quantity, stock)
                break
        flash('Cart updated.', 'success')

    _save_cart(cart)
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/cart/remove/<product_id>')
def remove_from_cart(product_id):
    cart = [i for i in _get_cart() if i['product_id'] != product_id]
    _save_cart(cart)
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/cart/clear')
def clear_cart():
    _save_cart([])
    flash('Cart cleared.', 'info')
    return redirect(url_for('product.home'))


@cart_bp.route('/cart/count')
def cart_count():
    """AJAX endpoint: return number of items in cart."""
    count = sum(i['quantity'] for i in _get_cart())
    return jsonify({'count': count})
