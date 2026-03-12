"""
services/subscription_service.py
Subscription plan management for HomeMade Pickles & Snacks.
Now backed by MongoDB Atlas.
"""

import uuid
import logging
from datetime import datetime, timedelta
from pymongo.errors import PyMongoError
from config.mongodb_config import get_collection
from services.user_service import update_user_subscription
import config.settings as settings

logger = logging.getLogger(__name__)
COL = settings.SUBSCRIPTIONS_COLLECTION


def _clean(doc: dict | None) -> dict | None:
    """Remove MongoDB's internal _id."""
    if doc:
        doc.pop('_id', None)
    return doc


def create_subscription(user_id: str, plan_key: str, address: str) -> dict:
    """
    Create a new subscription for a user.
    plan_key: 'weekly' | 'monthly'
    Returns {'success': True, 'subscription_id': ...} or error dict.
    """
    plans = settings.SUBSCRIPTION_PLANS
    if plan_key not in plans:
        return {'success': False, 'error': 'Invalid plan.'}

    plan = plans[plan_key]
    now = datetime.utcnow()
    next_delivery = now + timedelta(days=plan['delivery_days'])
    sub_id = str(uuid.uuid4())
    doc = {
        'subscription_id': sub_id,
        'user_id':         user_id,
        'plan_key':        plan_key,
        'plan_name':       plan['name'],
        'price':           float(plan['price']),
        'delivery_days':   plan['delivery_days'],
        'address':         address,
        'status':          'active',   # active | paused | cancelled
        'created_at':      now.isoformat(),
        'next_delivery':   next_delivery.isoformat(),
    }
    try:
        get_collection(COL).insert_one(doc)
        update_user_subscription(user_id, sub_id)
        logger.info(f"Subscription created: {sub_id} for user {user_id}")
        return {'success': True, 'subscription_id': sub_id}
    except PyMongoError as e:
        logger.error(f"create_subscription error: {e}")
        return {'success': False, 'error': str(e)}


def get_subscription_by_id(sub_id: str) -> dict | None:
    try:
        return _clean(get_collection(COL).find_one({'subscription_id': sub_id}))
    except PyMongoError as e:
        logger.error(f"get_subscription_by_id error: {e}")
        return None


def get_subscriptions_by_user(user_id: str) -> list:
    try:
        return [_clean(s) for s in get_collection(COL).find({'user_id': user_id})]
    except PyMongoError as e:
        logger.error(f"get_subscriptions_by_user error: {e}")
        return []


def update_subscription_status(sub_id: str, status: str) -> bool:
    allowed = {'active', 'paused', 'cancelled'}
    if status not in allowed:
        return False
    try:
        result = get_collection(COL).update_one(
            {'subscription_id': sub_id},
            {'$set': {'status': status}}
        )
        return result.matched_count > 0
    except PyMongoError as e:
        logger.error(f"update_subscription_status error: {e}")
        return False


def get_all_subscriptions() -> list:
    """Admin: all subscriptions."""
    try:
        return [_clean(s) for s in get_collection(COL).find({})]
    except PyMongoError as e:
        logger.error(f"get_all_subscriptions error: {e}")
        return []
