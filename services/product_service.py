"""
services/product_service.py
Product & inventory management for HomeMade Pickles & Snacks.
Now backed by DynamoDB.
"""

import uuid
import logging
from datetime import datetime
from botocore.exceptions import ClientError
from config.dynamodb_config import get_table
import config.settings as settings

logger = logging.getLogger(__name__)

PRODUCTS_TABLE = get_table(settings.PRODUCTS_TABLE)


# ── Read Operations ─────────────────────────────────────────────

def get_all_products(category=None):
    """Return all active products."""
    try:
        response = PRODUCTS_TABLE.scan()
        items = response.get("Items", [])

        items = [p for p in items if p.get("is_active", True)]

        if category:
            items = [p for p in items if p.get("category") == category]

        return items

    except ClientError as e:
        logger.error(f"get_all_products error: {e}")
        return []


def get_product_by_id(product_id):
    """Fetch product by ID."""
    try:
        response = PRODUCTS_TABLE.get_item(Key={"product_id": product_id})
        return response.get("Item")

    except ClientError as e:
        logger.error(f"get_product_by_id error: {e}")
        return None


def get_products_by_ids(product_ids):
    """Fetch multiple products."""
    return [get_product_by_id(pid) for pid in product_ids]


def get_featured_products(limit=6):
    """Return newest products."""
    products = get_all_products()
    products.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return products[:limit]


# ── Write Operations ─────────────────────────────────────────────

def add_product(name, description, price, category, stock, image_url="", weight=""):

    product_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    product = {
        "product_id": product_id,
        "name": name.strip(),
        "description": description.strip(),
        "price": float(price),
        "category": category,
        "stock": int(stock),
        "image_url": image_url,
        "weight": weight,
        "created_at": now,
        "is_active": True
    }

    try:
        PRODUCTS_TABLE.put_item(Item=product)
        logger.info(f"Product added: {name}")

        return {
            "success": True,
            "product_id": product_id
        }

    except ClientError as e:
        logger.error(f"add_product error: {e}")

        return {
            "success": False,
            "error": str(e)
        }


def update_product(product_id, fields):

    try:
        update_expr = "SET "
        expr_values = {}

        for i, (k, v) in enumerate(fields.items()):
            key = f":v{i}"
            update_expr += f"{k}={key},"
            expr_values[key] = v

        update_expr = update_expr.rstrip(",")

        PRODUCTS_TABLE.update_item(
            Key={"product_id": product_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )

        return True

    except ClientError as e:
        logger.error(f"update_product error: {e}")
        return False


def delete_product(product_id):
    """Soft delete product."""
    return update_product(product_id, {"is_active": False})


def update_stock(product_id, quantity_delta):

    try:
        product = get_product_by_id(product_id)

        if not product:
            raise ValueError("Product not found")

        new_stock = product.get("stock", 0) + quantity_delta

        if new_stock < 0:
            raise ValueError("Insufficient stock")

        PRODUCTS_TABLE.update_item(
            Key={"product_id": product_id},
            UpdateExpression="SET stock=:s",
            ExpressionAttributeValues={":s": new_stock}
        )

        return True

    except (ClientError, ValueError) as e:
        logger.error(f"update_stock error: {e}")
        return False


def deduct_stock_for_order(items):
    """Deduct stock when order is placed."""
    for item in items:
        update_stock(item["product_id"], -int(item["quantity"]))

    return True