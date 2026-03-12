"""
services/subscription_service.py
Subscription plan management for HomeMade Pickles & Snacks.
Now backed by DynamoDB.
"""

import uuid
import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from config.dynamodb_config import get_table
from services.user_service import update_user_subscription
import config.settings as settings

logger = logging.getLogger(__name__)

SUBSCRIPTIONS_TABLE = get_table(settings.SUBSCRIPTIONS_TABLE)


# ── Create Subscription ─────────────────────────────────────────

def create_subscription(user_id, plan_key, address):

    plans = settings.SUBSCRIPTION_PLANS

    if plan_key not in plans:
        return {"success": False, "error": "Invalid plan"}

    plan = plans[plan_key]

    now = datetime.utcnow()
    next_delivery = now + timedelta(days=plan["delivery_days"])

    sub_id = str(uuid.uuid4())

    subscription = {
        "subscription_id": sub_id,
        "user_id": user_id,
        "plan_key": plan_key,
        "plan_name": plan["name"],
        "price": float(plan["price"]),
        "delivery_days": plan["delivery_days"],
        "address": address,
        "status": "active",
        "created_at": now.isoformat(),
        "next_delivery": next_delivery.isoformat()
    }

    try:

        SUBSCRIPTIONS_TABLE.put_item(Item=subscription)

        update_user_subscription(user_id, sub_id)

        logger.info(f"Subscription created: {sub_id}")

        return {
            "success": True,
            "subscription_id": sub_id
        }

    except ClientError as e:

        logger.error(f"create_subscription error: {e}")

        return {
            "success": False,
            "error": str(e)
        }


# ── Read Operations ─────────────────────────────────────────────

def get_subscription_by_id(sub_id):

    try:

        response = SUBSCRIPTIONS_TABLE.get_item(
            Key={"subscription_id": sub_id}
        )

        return response.get("Item")

    except ClientError as e:

        logger.error(f"get_subscription_by_id error: {e}")

        return None


def get_subscriptions_by_user(user_id):

    try:

        response = SUBSCRIPTIONS_TABLE.scan()

        return [
            s for s in response.get("Items", [])
            if s.get("user_id") == user_id
        ]

    except ClientError as e:

        logger.error(f"get_subscriptions_by_user error: {e}")

        return []


# ── Update Operations ───────────────────────────────────────────

def update_subscription_status(sub_id, status):

    allowed = {"active", "paused", "cancelled"}

    if status not in allowed:
        return False

    try:

        SUBSCRIPTIONS_TABLE.update_item(
            Key={"subscription_id": sub_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": status}
        )

        return True

    except ClientError as e:

        logger.error(f"update_subscription_status error: {e}")

        return False


# ── Admin Operations ───────────────────────────────────────────

def get_all_subscriptions():

    try:

        response = SUBSCRIPTIONS_TABLE.scan()

        return response.get("Items", [])

    except ClientError as e:

        logger.error(f"get_all_subscriptions error: {e}")

        return []