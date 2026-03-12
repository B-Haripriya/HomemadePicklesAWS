"""
routes/order_routes.py
Checkout, order placement, confirmation, and order history.
"""

import logging
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash)
from services.order_service import (place_order, get_order_by_id,
                                    get_orders_by_user)
from functools import wraps

logger = logging.getLogger(__name__)
order_bp = Blueprint('order', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@order_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = session.get('cart', [])
    if not cart:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('product.home'))

    total = sum(i['price'] * i['quantity'] for i in cart)

    if request.method == 'POST':
        address        = request.form.get('address', '').strip()
        payment_method = request.form.get('payment_method', 'COD')

        if not address:
            flash('Please provide a delivery address.', 'danger')
            return render_template('order/checkout.html', cart=cart, total=total)

        # Build cart_items for order service
        order_items = [
            {
                'product_id': item['product_id'],
                'quantity':   item['quantity'],
                'price':      item['price'],
            }
            for item in cart
        ]

        result = place_order(
            user_id=session['user_id'],
            cart_items=order_items,
            address=address,
            payment_method=payment_method,
        )

        if result['success']:
            # Clear cart on successful order
            session['cart'] = []
            session.modified = True
            return redirect(url_for('order.order_confirmation',
                                    order_id=result['order_id'],
                                    msg=result['confirmation']))
        else:
            flash(result['error'], 'danger')

    return render_template('order/checkout.html', cart=cart, total=total)


@order_bp.route('/order/confirmation')
@login_required
def order_confirmation():
    order_id = request.args.get('order_id')
    msg      = request.args.get('msg', '')
    order    = get_order_by_id(order_id) if order_id else None
    return render_template('order/confirmation.html', order=order, msg=msg)


@order_bp.route('/orders')
@login_required
def order_history():
    orders = get_orders_by_user(session['user_id'])
    return render_template('order/order_history.html', orders=orders)


@order_bp.route('/orders/<order_id>')
@login_required
def order_detail(order_id):
    order = get_order_by_id(order_id)
    if not order or order.get('user_id') != session['user_id']:
        flash('Order not found.', 'warning')
        return redirect(url_for('order.order_history'))
    return render_template('order/order_detail.html', order=order)
