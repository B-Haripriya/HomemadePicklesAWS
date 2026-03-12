"""
services/order_service.py
Order placement, history, confirmation, and admin order management.
Now backed by MongoDB Atlas.
"""

import uuid
import logging
from datetime import datetime
from collections import defaultdict
from pymongo.errors import PyMongoError
from config.mongodb_config import get_collection
from services.product_service import deduct_stock_for_order, get_product_by_id
from services.user_service import update_user_orders
import config.settings as settings

logger = logging.getLogger(__name__)
COL = settings.ORDERS_COLLECTION


def _clean(doc: dict | None) -> dict | None:
    """Remove MongoDB's internal _id."""
    if doc:
        doc.pop('_id', None)
    return doc


def place_order(user_id: str, cart_items: list, address: str,
                payment_method: str = 'COD') -> dict:
    """
    Place an order:
      1. Validate stock for each item.
      2. Deduct inventory (atomic per item).
      3. Simulate payment.
      4. Persist order to MongoDB.
      5. Link order to user profile.

    cart_items: [{'product_id': ..., 'quantity': ..., 'price': ...}, ...]
    Returns {'success': True, 'order_id': ..., 'confirmation': ...} or error dict.
    """
    # ── Enrich cart with product names ────────────────────────────────────────
    enriched_items = []
    total = 0.0
    for ci in cart_items:
        product = get_product_by_id(ci['product_id'])
        if not product:
            return {'success': False, 'error': f"Product {ci['product_id']} not found."}
        qty = int(ci['quantity'])
        if product.get('stock', 0) < qty:
            return {
                'success': False,
                'error': (f"Insufficient stock for '{product['name']}'. "
                          f"Only {product['stock']} left.")
            }
        unit_price = round(float(product['price']), 2)
        subtotal = round(unit_price * qty, 2)
        enriched_items.append({
            'product_id':   ci['product_id'],
            'product_name': product['name'],
            'quantity':     qty,
            'unit_price':   unit_price,
            'subtotal':     subtotal,
        })
        total += subtotal

    total = round(total, 2)

    # ── Deduct inventory ───────────────────────────────────────────────────────
    try:
        deduct_stock_for_order(enriched_items)
    except ValueError as ve:
        return {'success': False, 'error': str(ve)}

    # ── Simulate payment ───────────────────────────────────────────────────────
    payment_status = 'paid' if settings.PAYMENT_SIMULATION else 'pending'

    # ── Persist order ──────────────────────────────────────────────────────────
    order_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    order = {
        'order_id':       order_id,
        'user_id':        user_id,
        'items':          enriched_items,
        'total_amount':   total,
        'address':        address,
        'payment_method': payment_method,
        'payment_status': payment_status,
        'order_status':   'confirmed',   # confirmed | dispatched | delivered | cancelled
        'created_at':     now,
        'updated_at':     now,
    }
    try:
        get_collection(COL).insert_one(order)
        update_user_orders(user_id, order_id)
        logger.info(f"Order placed: {order_id} by user {user_id}")
        confirmation_msg = (
            f"🎉 Order #{order_id[:8].upper()} confirmed! "
            f"Total ₹{total:.2f}. "
            f"Expected delivery in 3–5 business days."
        )
        return {
            'success':      True,
            'order_id':     order_id,
            'confirmation': confirmation_msg,
            'total':        total,
        }
    except PyMongoError as e:
        logger.error(f"place_order insert error: {e}")
        return {'success': False, 'error': 'Could not save order. Please try again.'}


def get_order_by_id(order_id: str) -> dict | None:
    """Fetch a single order."""
    try:
        return _clean(get_collection(COL).find_one({'order_id': order_id}))
    except PyMongoError as e:
        logger.error(f"get_order_by_id error: {e}")
        return None


def get_orders_by_user(user_id: str) -> list:
    """Return all orders for a given user, newest first."""
    try:
        return [
            _clean(o)
            for o in get_collection(COL)
            .find({'user_id': user_id})
            .sort('created_at', -1)
        ]
    except PyMongoError as e:
        logger.error(f"get_orders_by_user error: {e}")
        return []


def get_all_orders() -> list:
    """Admin: return all orders, newest first."""
    try:
        return [
            _clean(o)
            for o in get_collection(COL).find({}).sort('created_at', -1)
        ]
    except PyMongoError as e:
        logger.error(f"get_all_orders error: {e}")
        return []


def update_order_status(order_id: str, status: str) -> bool:
    """Admin: update order lifecycle status."""
    allowed = {'confirmed', 'dispatched', 'delivered', 'cancelled'}
    if status not in allowed:
        return False
    try:
        result = get_collection(COL).update_one(
            {'order_id': order_id},
            {'$set': {'order_status': status, 'updated_at': datetime.utcnow().isoformat()}}
        )
        return result.matched_count > 0
    except PyMongoError as e:
        logger.error(f"update_order_status error: {e}")
        return False


def get_sales_stats() -> dict:
    """Admin dashboard: compute aggregate sales statistics."""
    orders = get_all_orders()
    total_revenue = sum(o.get('total_amount', 0) for o in orders)
    status_counts: dict = {}
    for o in orders:
        s = o.get('order_status', 'unknown')
        status_counts[s] = status_counts.get(s, 0) + 1

    # Revenue by day (last 7 days)
    daily: dict = defaultdict(float)
    for o in orders:
        day = o.get('created_at', '')[:10]   # YYYY-MM-DD
        daily[day] += o.get('total_amount', 0)

    return {
        'total_orders':  len(orders),
        'total_revenue': round(total_revenue, 2),
        'status_counts': status_counts,
        'daily_revenue': dict(sorted(daily.items())[-7:]),
    }
