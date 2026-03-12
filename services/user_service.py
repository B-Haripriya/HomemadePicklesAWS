"""
services/user_service.py
User registration, login, and profile management using DynamoDB.
"""

import uuid
import hashlib
import hmac
import os
import logging
from datetime import datetime
from botocore.exceptions import ClientError
from config.dynamodb_config import get_table
import config.settings as settings

logger = logging.getLogger(__name__)

USERS_TABLE = get_table(settings.USERS_TABLE)


# ── Password Utilities ─────────────────────────────

def _hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310000)
    return salt.hex() + ":" + key.hex()


def _verify_password(stored_hash: str, password: str) -> bool:
    try:
        salt_hex, key_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(key_hex)

        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310000)
        return hmac.compare_digest(key, expected)
    except Exception:
        return False


# ── User Operations ─────────────────────────────

def register_user(name, email, password, phone=""):

    user_id = str(uuid.uuid4())

    user = {
        "user_id": user_id,
        "name": name,
        "email": email.lower(),
        "phone": phone,
        "password_hash": _hash_password(password),
        "role": "customer",
        "created_at": datetime.utcnow().isoformat(),
        "order_ids": []
    }

    try:
        USERS_TABLE.put_item(Item=user)
        return {"success": True, "user_id": user_id}

    except ClientError as e:
        logger.error(e)
        return {"success": False, "error": str(e)}


def login_user(email, password):

    try:
        response = USERS_TABLE.scan(
            FilterExpression="email = :e",
            ExpressionAttributeValues={":e": email.lower()}
        )

        users = response.get("Items", [])

        if not users:
            return None

        user = users[0]

        if _verify_password(user["password_hash"], password):
            return user

        return None

    except ClientError as e:
        logger.error(e)
        return None


def get_user_by_id(user_id):

    try:
        response = USERS_TABLE.get_item(Key={"user_id": user_id})
        return response.get("Item")

    except ClientError as e:
        logger.error(e)
        return None


def update_user_orders(user_id, order_id):

    try:
        USERS_TABLE.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET order_ids = list_append(order_ids, :o)",
            ExpressionAttributeValues={
                ":o": [order_id]
            }
        )

    except ClientError as e:
        logger.error(e)
def get_all_users():
    """
    Admin: fetch all users from DynamoDB
    """
    try:
        response = USERS_TABLE.scan()
        users = response.get("Items", [])
        return users

    except ClientError as e:
        logger.error(f"get_all_users error: {e}")
        return []