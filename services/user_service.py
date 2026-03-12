"""
services/user_service.py
Business logic for user registration, login, and profile management.
Now backed by MongoDB Atlas.
"""

import uuid
import hashlib
import hmac
import os
import logging
from datetime import datetime
from pymongo.errors import DuplicateKeyError, PyMongoError
from config.mongodb_config import get_collection
import config.settings as settings

logger = logging.getLogger(__name__)
COL = settings.USERS_COLLECTION


# ── Password Utilities ─────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Return a secure PBKDF2-HMAC-SHA256 hash with embedded salt."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310_000)
    return salt.hex() + ':' + key.hex()


def _verify_password(stored_hash: str, password: str) -> bool:
    """Verify a plaintext password against the stored hash."""
    try:
        salt_hex, key_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310_000)
        return hmac.compare_digest(key, expected_key)
    except Exception:
        return False


# ── Helpers ────────────────────────────────────────────────────────────────────

def _clean(doc: dict | None) -> dict | None:
    """Remove MongoDB's internal _id before returning a document."""
    if doc:
        doc.pop('_id', None)
    return doc


# ── CRUD Operations ────────────────────────────────────────────────────────────

def register_user(name: str, email: str, password: str, phone: str = '') -> dict:
    """
    Register a new user.
    Returns {'success': True, 'user_id': ...} or {'success': False, 'error': '...'}.
    """
    col = get_collection(COL)
    email = email.lower().strip()

    # Duplicate-email check (handled by unique index, but we give a friendly msg)
    if col.find_one({'email': email}, {'_id': 1}):
        return {'success': False, 'error': 'Email already registered.'}

    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    doc = {
        'user_id':         user_id,
        'name':            name.strip(),
        'email':           email,
        'phone':           phone.strip(),
        'password_hash':   _hash_password(password),
        'role':            'customer',   # 'customer' | 'admin'
        'created_at':      now,
        'order_ids':       [],
        'subscription_id': None,
    }
    try:
        col.insert_one(doc)
        logger.info(f"New user registered: {email}")
        return {'success': True, 'user_id': user_id}
    except DuplicateKeyError:
        return {'success': False, 'error': 'Email already registered.'}
    except PyMongoError as e:
        logger.error(f"register_user error: {e}")
        return {'success': False, 'error': 'Database error.'}


def login_user(email: str, password: str) -> dict | None:
    """Validate credentials. Returns user data dict or None."""
    try:
        user = get_collection(COL).find_one({'email': email.lower().strip()})
        if not user:
            return None
        if _verify_password(user['password_hash'], password):
            return _clean(user)
        return None
    except PyMongoError as e:
        logger.error(f"login_user error: {e}")
        return None


def get_user_by_id(user_id: str) -> dict | None:
    """Fetch a user by user_id."""
    try:
        return _clean(get_collection(COL).find_one({'user_id': user_id}))
    except PyMongoError as e:
        logger.error(f"get_user_by_id error: {e}")
        return None


def update_user_orders(user_id: str, order_id: str):
    """Append an order_id to the user's order list."""
    try:
        get_collection(COL).update_one(
            {'user_id': user_id},
            {'$push': {'order_ids': order_id}}
        )
    except PyMongoError as e:
        logger.error(f"update_user_orders error: {e}")


def update_user_subscription(user_id: str, subscription_id: str):
    """Link a subscription to a user."""
    try:
        get_collection(COL).update_one(
            {'user_id': user_id},
            {'$set': {'subscription_id': subscription_id}}
        )
    except PyMongoError as e:
        logger.error(f"update_user_subscription error: {e}")


def get_all_users() -> list:
    """Admin: retrieve all users."""
    try:
        return [_clean(u) for u in get_collection(COL).find({}, {'password_hash': 0})]
    except PyMongoError as e:
        logger.error(f"get_all_users error: {e}")
        return []


def seed_admin(email='admin@pickles.com', password='Admin@1234'):
    """
    Create a default admin user if one doesn't already exist.
    Call this from a management script or on first startup.
    """
    col = get_collection(COL)
    try:
        if col.find_one({'email': email}):
            return  # already exists
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        col.insert_one({
            'user_id':         user_id,
            'name':            'Admin',
            'email':           email,
            'phone':           '',
            'password_hash':   _hash_password(password),
            'role':            'admin',
            'created_at':      now,
            'order_ids':       [],
            'subscription_id': None,
        })
        logger.info(f"Admin user seeded: {email}")
    except PyMongoError as e:
        logger.error(f"seed_admin error: {e}")
