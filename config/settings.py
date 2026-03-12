"""
config/settings.py
Central settings for HomeMade Pickles & Snacks application.
Override these values via environment variables or a .env file.
"""

import os
from dotenv import load_dotenv

# Load .env file if present (development convenience)
load_dotenv()

# ── Security ───────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production-32chars!!')
SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV', 'development') == 'production'

# ── App Mode ───────────────────────────────────────────────────────────────────
DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

# ── MongoDB Atlas ──────────────────────────────────────────────────────────────
# Paste your Atlas connection string here or set the MONGO_URI environment variable.
# Format: mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGO_URI     = os.environ.get('MONGO_URI', 'mongodb+srv://CHANGE_ME:CHANGE_ME@cluster0.example.mongodb.net/?retryWrites=true&w=majority')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'pickles_db')

# ── Collection Names ───────────────────────────────────────────────────────────
USERS_COLLECTION         = 'users'
PRODUCTS_COLLECTION      = 'products'
ORDERS_COLLECTION        = 'orders'
SUBSCRIPTIONS_COLLECTION = 'subscriptions'

# ── CloudWatch Logging (optional – only used when running on AWS) ───────────────
ENABLE_CLOUDWATCH      = os.environ.get('ENABLE_CLOUDWATCH', 'False').lower() == 'true'
CLOUDWATCH_LOG_GROUP   = os.environ.get('CLOUDWATCH_LOG_GROUP', '/pickles-app/flask')
CLOUDWATCH_STREAM_NAME = os.environ.get('CLOUDWATCH_STREAM_NAME', 'app-stream')
AWS_REGION             = os.environ.get('AWS_REGION', 'us-east-1')

# ── Payment Simulation ─────────────────────────────────────────────────────────
PAYMENT_SIMULATION = True   # Set False when integrating real payment gateway

# ── Subscription Plans ─────────────────────────────────────────────────────────
SUBSCRIPTION_PLANS = {
    'weekly': {
        'name': 'Weekly Delight',
        'price': 299,
        'delivery_days': 7,
        'description': 'Fresh pickles & snacks every week!'
    },
    'monthly': {
        'name': 'Monthly Bonanza',
        'price': 999,
        'delivery_days': 30,
        'description': 'Big savings with monthly delivery!'
    }
}

# ── Product Categories ─────────────────────────────────────────────────────────
CATEGORIES = ['Pickles', 'Snacks', 'Combos', 'Gift Packs']

# ── Currency ───────────────────────────────────────────────────────────────────
CURRENCY_SYMBOL = '₹'
# AWS region
AWS_REGION = "us-east-1"

# DynamoDB tables
USERS_TABLE = "users"
PRODUCTS_TABLE = "products"
ORDERS_TABLE = "orders"
SUBSCRIPTIONS_TABLE = "subscriptions"
CART_TABLE = "cart"
REVIEWS_TABLE = "reviews"
