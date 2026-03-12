"""
services/order_service.py
Order placement, history, confirmation, and admin order management.
Now backed by DynamoDB.
"""

import uuid
import logging
from datetime import datetime
from collections import defaultdict
from botocore.exceptions import ClientError
from config.dynamodb_config import get_table
from services.product_service import deduct_stock_for_order, get_product_by_id
from services.user_service import update_user_orders
import config.settings as settings

logger = logging.getLogger(__name__)

ORDERS_TABLE = get_table(settings.ORDERS_TABLE)


# ── Order Placement ─────────────────────────────────────────────

def place_order(user_id, cart_items, address, payment_method="COD"):

    enriched_items = []
    total = 0.0

    for ci in cart_items:

        product = get_product_by_id(ci["product_id"])

        if not product:
            return {"success": False, "error": "Product not found"}

        qty = int(ci["quantity"])

        if product.get("stock", 0) < qty:
            return {
                "success": False,
                "error": f"Insufficient stock for {product['name']}"
            }

        price = float(product["price"])
        subtotal = price * qty

        enriched_items.append({
            "product_id": ci["product_id"],
            "product_name": product["name"],
            "quantity": qty,
            "unit_price": price,
            "subtotal": subtotal
        })

        total += subtotal

    total = round(total, 2)

    try:
        deduct_stock_for_order(enriched_items)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    payment_status = "paid" if settings.PAYMENT_SIMULATION else "pending"

    order_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    order = {
        "order_id": order_id,
        "user_id": user_id,
        "items": enriched_items,
        "total_amount": total,
        "address": address,
        "payment_method": payment_method,
        "payment_status": payment_status,
        "order_status": "confirmed",
        "created_at": now,
        "updated_at": now
    }

    try:
        ORDERS_TABLE.put_item(Item=order)

        update_user_orders(user_id, order_id)

        logger.info(f"Order placed: {order_id}")

        return {
            "success": True,
            "order_id": order_id,
            "total": total
        }

    except ClientError as e:
        logger.error(f"place_order error: {e}")

        return {
            "success": False,
            "error": "Could not save order"
        }


# ── Read Operations ─────────────────────────────────────────────

def get_order_by_id(order_id):

    try:
        response = ORDERS_TABLE.get_item(Key={"order_id": order_id})
        return response.get("Item")

    except ClientError as e:
        logger.error(f"get_order_by_id error: {e}")
        return None


def get_orders_by_user(user_id):

    try:
        response = ORDERS_TABLE.scan()

        return [
            o for o in response.get("Items", [])
            if o.get("user_id") == user_id
        ]

    except ClientError as e:
        logger.error(f"get_orders_by_user error: {e}")
        return []


def get_all_orders():

    try:
        response = ORDERS_TABLE.scan()
        return response.get("Items", [])

    except ClientError as e:
        logger.error(f"get_all_orders error: {e}")
        return []


# ── Update Operations ───────────────────────────────────────────

def update_order_status(order_id, status):

    allowed = {"confirmed", "dispatched", "delivered", "cancelled"}

    if status not in allowed:
        return False

    try:
        ORDERS_TABLE.update_item(
            Key={"order_id": order_id},
            UpdateExpression="SET order_status=:s, updated_at=:u",
            ExpressionAttributeValues={
                ":s": status,
                ":u": datetime.utcnow().isoformat()
            }
        )

        return True

    except ClientError as e:
        logger.error(f"update_order_status error: {e}")
        return False


# ── Sales Statistics ────────────────────────────────────────────

def get_sales_stats():

    orders = get_all_orders()

    total_revenue = sum(o.get("total_amount", 0) for o in orders)

    status_counts = {}

    for o in orders:
        s = o.get("order_status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    daily = defaultdict(float)

    for o in orders:
        day = o.get("created_at", "")[:10]
        daily[day] += o.get("total_amount", 0)

    return {
        "total_orders": len(orders),
        "total_revenue": round(total_revenue, 2),
        "status_counts": status_counts,
        "daily_revenue": dict(sorted(daily.items())[-7:])
    }