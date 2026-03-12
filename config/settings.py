"""
config/settings.py
Central settings for HomeMade Pickles & Snacks application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# ── Security ─────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production-32chars!!")
SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV", "development") == "production"

# ── App Mode ─────────────────────────────────────────────
DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() == "true"

# ── AWS Configuration ────────────────────────────────────
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Optional AWS credentials (not required if using EC2 IAM role)
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# ── DynamoDB Table Names ─────────────────────────────────
USERS_TABLE = "users"
PRODUCTS_TABLE = "products"
ORDERS_TABLE = "orders"
SUBSCRIPTIONS_TABLE = "subscriptions"
CART_TABLE = "cart"
REVIEWS_TABLE = "reviews"

# ── CloudWatch Logging (optional) ────────────────────────
ENABLE_CLOUDWATCH = os.environ.get("ENABLE_CLOUDWATCH", "False").lower() == "true"
CLOUDWATCH_LOG_GROUP = os.environ.get("CLOUDWATCH_LOG_GROUP", "/pickles-app/flask")
CLOUDWATCH_STREAM_NAME = os.environ.get("CLOUDWATCH_STREAM_NAME", "app-stream")

# ── Payment Simulation ───────────────────────────────────
PAYMENT_SIMULATION = True

# ── Subscription Plans ───────────────────────────────────
SUBSCRIPTION_PLANS = {
    "weekly": {
        "name": "Weekly Delight",
        "price": 299,
        "delivery_days": 7,
        "description": "Fresh pickles & snacks every week!"
    },
    "monthly": {
        "name": "Monthly Bonanza",
        "price": 999,
        "delivery_days": 30,
        "description": "Big savings with monthly delivery!"
    }
}

# ── Product Categories ───────────────────────────────────
CATEGORIES = ["Pickles", "Snacks", "Combos", "Gift Packs"]

# ── Currency ─────────────────────────────────────────────
CURRENCY_SYMBOL = "₹"