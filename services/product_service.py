"""
services/product_service.py
Product & inventory management for HomeMade Pickles & Snacks.
Now backed by MongoDB Atlas.
"""

import uuid
import logging
from datetime import datetime
from pymongo.errors import PyMongoError
from config.mongodb_config import get_collection
import config.settings as settings

logger = logging.getLogger(__name__)
COL = settings.PRODUCTS_COLLECTION


# ── Helper ─────────────────────────────────────────────────────────────────────

def _clean(doc: dict | None) -> dict | None:
    """Remove MongoDB's internal _id."""
    if doc:
        doc.pop('_id', None)
    return doc


# ── Read Operations ────────────────────────────────────────────────────────────

def get_all_products(category: str = None) -> list:
    """Return all active products, optionally filtered by category."""
    try:
        query = {'is_active': True}
        if category:
            query['category'] = category
        return [_clean(p) for p in get_collection(COL).find(query)]
    except PyMongoError as e:
        logger.error(f"get_all_products error: {e}")
        return []


def get_product_by_id(product_id: str) -> dict | None:
    """Fetch a single product by product_id."""
    try:
        return _clean(get_collection(COL).find_one({'product_id': product_id}))
    except PyMongoError as e:
        logger.error(f"get_product_by_id error: {e}")
        return None


def get_products_by_ids(product_ids: list) -> list:
    """Batch-fetch multiple products."""
    return [p for pid in product_ids if (p := get_product_by_id(pid))]


def get_featured_products(limit: int = 6) -> list:
    """Return newest active products for the homepage."""
    try:
        return [
            _clean(p)
            for p in get_collection(COL)
            .find({'is_active': True})
            .sort('created_at', -1)
            .limit(limit)
        ]
    except PyMongoError as e:
        logger.error(f"get_featured_products error: {e}")
        return []


def get_recommendations(order_history: list, limit: int = 4) -> list:
    """
    Personalized recommendations based on categories from past orders.
    Falls back to latest products when no history is available.
    """
    if not order_history:
        return get_featured_products(limit)

    seen_categories = set()
    ordered_pids = set()
    for order in order_history:
        for item in order.get('items', []):
            pid = item.get('product_id')
            if pid:
                ordered_pids.add(pid)
                p = get_product_by_id(pid)
                if p:
                    seen_categories.add(p.get('category'))

    recommended = []
    if seen_categories:
        try:
            cursor = get_collection(COL).find({
                'is_active': True,
                'category': {'$in': list(seen_categories)},
                'product_id': {'$nin': list(ordered_pids)},
            }).limit(limit)
            recommended = [_clean(p) for p in cursor]
        except PyMongoError as e:
            logger.error(f"get_recommendations error: {e}")

    if len(recommended) < limit:
        pad = [p for p in get_featured_products(limit * 2) if p not in recommended]
        recommended = (recommended + pad)[:limit]

    return recommended


# ── Write Operations ───────────────────────────────────────────────────────────

def add_product(name: str, description: str, price: float, category: str,
                stock: int, image_url: str = '', weight: str = '') -> dict:
    """Admin: create a new product."""
    product_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    doc = {
        'product_id':  product_id,
        'name':        name.strip(),
        'description': description.strip(),
        'price':       round(float(price), 2),
        'category':    category,
        'stock':       int(stock),
        'image_url':   image_url,
        'weight':      weight,
        'created_at':  now,
        'is_active':   True,
    }
    try:
        get_collection(COL).insert_one(doc)
        logger.info(f"Product added: {name} ({product_id})")
        return {'success': True, 'product_id': product_id}
    except PyMongoError as e:
        logger.error(f"add_product error: {e}")
        return {'success': False, 'error': str(e)}


def update_product(product_id: str, fields: dict) -> bool:
    """Admin: update arbitrary product fields."""
    if not fields:
        return False
    # Convert float prices to plain float (no Decimal needed in Mongo)
    sanitized = {k: round(float(v), 2) if isinstance(v, float) else v
                 for k, v in fields.items()}
    try:
        result = get_collection(COL).update_one(
            {'product_id': product_id},
            {'$set': sanitized}
        )
        return result.matched_count > 0
    except PyMongoError as e:
        logger.error(f"update_product error: {e}")
        return False


def delete_product(product_id: str) -> bool:
    """Admin: soft-delete a product (mark inactive)."""
    return update_product(product_id, {'is_active': False})


def update_stock(product_id: str, quantity_delta: int) -> bool:
    """
    Atomically adjust stock. Raises ValueError when stock would go negative.
    Returns True on success.
    """
    try:
        col = get_collection(COL)
        # Only apply if resulting stock >= 0
        result = col.update_one(
            {'product_id': product_id,
             'stock': {'$gte': abs(quantity_delta) if quantity_delta < 0 else 0}},
            {'$inc': {'stock': quantity_delta}}
        )
        if result.matched_count == 0:
            logger.warning(f"Insufficient stock for product {product_id}")
            raise ValueError('Insufficient stock.')
        return True
    except ValueError:
        raise
    except PyMongoError as e:
        logger.error(f"update_stock error: {e}")
        return False


def deduct_stock_for_order(items: list) -> bool:
    """
    Deduct stock for each item in an order.
    `items` is a list of dicts: [{'product_id': ..., 'quantity': ...}, ...]
    Raises ValueError if any product has insufficient stock.
    """
    for item in items:
        update_stock(item['product_id'], -int(item['quantity']))
    return True


def seed_products():
    """Seed the database with sample products (skips if products already exist)."""
    col = get_collection(COL)
    if col.count_documents({}) > 0:
        logger.info("Products already seeded — skipping.")
        return
    samples = [
        # Pickles
        dict(name='Mango Pickle (Aam ka Achar)', description='Traditional sun-dried mango pickle with whole spices.', price=149.00, category='Pickles', stock=50, weight='500g'),
        dict(name='Mixed Vegetable Pickle', description='A medley of carrots, turnip, red chilli in mustard oil.', price=129.00, category='Pickles', stock=40, weight='500g'),
        dict(name='Lemon Pickle (Nimbu Achar)', description='Tangy lemon pickle with green chillies and turmeric.', price=99.00, category='Pickles', stock=60, weight='250g'),
        dict(name='Garlic Pickle', description='Pungent garlic cloves in spiced oil — an all-time favourite.', price=179.00, category='Pickles', stock=35, weight='300g'),
        dict(name='Green Chilli Pickle', description='Fiery green chilli pickle for heat lovers.', price=89.00, category='Pickles', stock=45, weight='250g'),
        dict(name='Raw Mango & Ginger Pickle', description='Seasonal raw mango with fresh ginger in sesame oil.', price=159.00, category='Pickles', stock=30, weight='400g'),
        # Snacks
        dict(name='Masala Chakli', description='Crispy spiral snack made with rice flour and whole spices.', price=119.00, category='Snacks', stock=70, weight='200g'),
        dict(name='Besan Sev (Thick)', description='Crunchy gram flour noodle snack with ajwain twist.', price=89.00, category='Snacks', stock=80, weight='200g'),
        dict(name='Spicy Mixture', description='A festive blend of sev, puffed rice, and peanuts.', price=99.00, category='Snacks', stock=65, weight='250g'),
        dict(name='Mathri', description='Flaky, crispy wheat biscuits with black pepper.', price=109.00, category='Snacks', stock=55, weight='200g'),
        # Combos
        dict(name='Pickle + Snacks Starter Pack', description='Best of both worlds — 1 mango pickle + 1 chakli pack.', price=239.00, category='Combos', stock=25, weight='700g'),
        # Gift Packs
        dict(name='Festival Gift Hamper', description='Curated collection of 3 pickles and 2 snack packs in a wicker basket.', price=549.00, category='Gift Packs', stock=15, weight='1.5kg'),
    ]
    for s in samples:
        add_product(**s)
    logger.info("Sample products seeded.")
