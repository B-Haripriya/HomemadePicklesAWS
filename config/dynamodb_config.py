"""
config/dynamodb_config.py
DynamoDB connection and table initialization for HomeMade Pickles & Snacks.
"""

import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
import config.settings as settings

logger = logging.getLogger(__name__)

def get_dynamodb_resource():
    """Return a boto3 DynamoDB resource. Supports local endpoint for dev."""
    kwargs = dict(
        region_name=settings.AWS_REGION,
        # Always pass credentials; fall back to dummy values so boto3 never
        # raises NoCredentialsError – real AWS will return an auth error
        # (ClientError) which service functions already handle gracefully.
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or 'local',
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or 'local',
    )
    if settings.DYNAMODB_ENDPOINT:
        kwargs['endpoint_url'] = settings.DYNAMODB_ENDPOINT
    return boto3.resource('dynamodb', **kwargs)


def get_dynamodb_client():
    """Return a low-level DynamoDB client."""
    kwargs = dict(
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or 'local',
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or 'local',
    )
    if settings.DYNAMODB_ENDPOINT:
        kwargs['endpoint_url'] = settings.DYNAMODB_ENDPOINT
    return boto3.client('dynamodb', **kwargs)


# ── Shared resource singleton ──────────────────────────────────────────────────
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


# ── Table Schemas ──────────────────────────────────────────────────────────────
TABLE_DEFINITIONS = [
    {
        'TableName': settings.USERS_TABLE,
        'KeySchema': [{'AttributeName': 'UserID', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [{'AttributeName': 'UserID', 'AttributeType': 'S'}],
        'BillingMode': 'PAY_PER_REQUEST',
    },
    {
        'TableName': settings.PRODUCTS_TABLE,
        'KeySchema': [{'AttributeName': 'ProductID', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [{'AttributeName': 'ProductID', 'AttributeType': 'S'}],
        'BillingMode': 'PAY_PER_REQUEST',
    },
    {
        'TableName': settings.ORDERS_TABLE,
        'KeySchema': [{'AttributeName': 'OrderID', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [{'AttributeName': 'OrderID', 'AttributeType': 'S'}],
        'BillingMode': 'PAY_PER_REQUEST',
    },
    {
        'TableName': settings.SUBSCRIPTIONS_TABLE,
        'KeySchema': [{'AttributeName': 'SubscriptionID', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [{'AttributeName': 'SubscriptionID', 'AttributeType': 'S'}],
        'BillingMode': 'PAY_PER_REQUEST',
    },
]


def init_tables():
    """
    Create DynamoDB tables if they don't already exist.
    Safe to call on every startup — skips already-existing tables.
    """
    client = get_dynamodb_client()
    existing = client.list_tables()['TableNames']

    for defn in TABLE_DEFINITIONS:
        name = defn['TableName']
        if name not in existing:
            try:
                db().create_table(**defn)
                logger.info(f"Created DynamoDB table: {name}")
            except ClientError as e:
                logger.error(f"Failed to create table {name}: {e}")
        else:
            logger.info(f"Table already exists: {name}")
