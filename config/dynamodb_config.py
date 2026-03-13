"""
config/dynamodb_config.py
DynamoDB connection and table initialization for HomeMade Pickles & Snacks.
"""

import boto3
import logging
from botocore.exceptions import ClientError
import config.settings as settings

logger = logging.getLogger(__name__)

# ── DynamoDB Resource ─────────────────────────────────────

def get_dynamodb_resource():
    """
    Create DynamoDB resource.
    When running on EC2 with IAM role, boto3 automatically
    retrieves credentials from the instance metadata service.
    """
    try:
        if settings.DYNAMODB_ENDPOINT:
            return boto3.resource(
                "dynamodb",
                region_name=settings.AWS_REGION,
                endpoint_url=settings.DYNAMODB_ENDPOINT
            )
        else:
            return boto3.resource(
                "dynamodb",
                region_name=settings.AWS_REGION
            )
    except ClientError as e:
        logger.error(f"DynamoDB connection error: {e}")
        raise


def get_dynamodb_client():
    """Return a low-level DynamoDB client."""
    try:
        if settings.DYNAMODB_ENDPOINT:
            return boto3.client(
                "dynamodb",
                region_name=settings.AWS_REGION,
                endpoint_url=settings.DYNAMODB_ENDPOINT
            )
        else:
            return boto3.client(
                "dynamodb",
                region_name=settings.AWS_REGION
            )
    except ClientError as e:
        logger.error(f"DynamoDB client error: {e}")
        raise


# ── Shared resource singleton ─────────────────────────────

_dynamodb = None

def db():
    """Get (or create) the shared DynamoDB resource."""
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = get_dynamodb_resource()
    return _dynamodb


def get_table(table_name: str):
    """Return a DynamoDB Table object."""
    return db().Table(table_name)


# ── Table Schemas ─────────────────────────────────────────

TABLE_DEFINITIONS = [
    {
        "TableName": settings.USERS_TABLE,
        "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "user_id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": settings.PRODUCTS_TABLE,
        "KeySchema": [{"AttributeName": "product_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "product_id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": settings.ORDERS_TABLE,
        "KeySchema": [{"AttributeName": "order_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "order_id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": settings.SUBSCRIPTIONS_TABLE,
        "KeySchema": [{"AttributeName": "subscription_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "subscription_id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
]


# ── Initialize Tables ─────────────────────────────────────

def init_tables():
    """
    Create DynamoDB tables if they don't already exist.
    Safe to call on every startup.
    """
    client = get_dynamodb_client()

    try:
        existing = client.list_tables()["TableNames"]
    except ClientError as e:
        logger.error(f"DynamoDB list_tables error: {e}")
        return

    for definition in TABLE_DEFINITIONS:
        name = definition["TableName"]

        if name not in existing:
            try:
                db().create_table(**definition)
                logger.info(f"Created DynamoDB table: {name}")
            except ClientError as e:
                logger.error(f"Failed to create table {name}: {e}")
        else:
            logger.info(f"Table already exists: {name}")