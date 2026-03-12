"""
config/mongodb_config.py
MongoDB Atlas connection and collection helpers for HomeMade Pickles & Snacks.
"""

import logging
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ConfigurationError
import config.settings as settings

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_db = None


def get_client() -> MongoClient:
    """Return the shared MongoClient (lazy singleton)."""
    global _client
    if _client is None:
        try:
            _client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
            # Verify connection
            _client.admin.command('ping')
            logger.info("Connected to MongoDB Atlas successfully.")
        except (ConnectionFailure, ConfigurationError) as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    return _client


def get_db():
    """Return the application database."""
    global _db
    if _db is None:
        _db = get_client()[settings.MONGO_DB_NAME]
    return _db


def get_collection(name: str):
    """Return a named collection from the application database."""
    return get_db()[name]


# ── Initialise indexes on startup ──────────────────────────────────────────────

def init_db():
    """
    Create indexes for all collections.
    Safe to call on every startup — MongoDB ignores already-existing indexes.
    """
    db = get_db()

    # Users
    db[settings.USERS_COLLECTION].create_index(
        [('email', ASCENDING)], unique=True, name='email_unique'
    )
    db[settings.USERS_COLLECTION].create_index('user_id', name='user_id_idx')

    # Products
    db[settings.PRODUCTS_COLLECTION].create_index('product_id', unique=True, name='product_id_unique')
    db[settings.PRODUCTS_COLLECTION].create_index('category', name='category_idx')

    # Orders
    db[settings.ORDERS_COLLECTION].create_index('order_id', unique=True, name='order_id_unique')
    db[settings.ORDERS_COLLECTION].create_index('user_id', name='order_user_idx')

    # Subscriptions
    db[settings.SUBSCRIPTIONS_COLLECTION].create_index(
        'subscription_id', unique=True, name='sub_id_unique'
    )
    db[settings.SUBSCRIPTIONS_COLLECTION].create_index('user_id', name='sub_user_idx')

    logger.info("MongoDB indexes verified / created.")
