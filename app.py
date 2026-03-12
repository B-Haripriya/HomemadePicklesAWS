"""
HomeMade Pickles & Snacks – Taste the Best
Main Flask Application Entry Point
"""

import logging
from flask import Flask
from config.dynamodb_config import init_tables
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.cart_routes import cart_bp
from routes.order_routes import order_bp
from routes.admin_routes import admin_bp
from routes.subscription_routes import subscription_bp
import config.settings as settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)

    app.secret_key = settings.SECRET_KEY
    app.config['SESSION_COOKIE_SECURE'] = settings.SESSION_COOKIE_SECURE
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    #  AWS CloudWatch Logging (Optional) 
    if settings.ENABLE_CLOUDWATCH:
        try:
            import watchtower
            cw_handler = watchtower.CloudWatchLogHandler(
                log_group=settings.CLOUDWATCH_LOG_GROUP,
                stream_name=settings.CLOUDWATCH_STREAM_NAME,
                region_name=settings.AWS_REGION
            )
            cw_handler.setLevel(logging.INFO)
            app.logger.addHandler(cw_handler)
            logger.info("CloudWatch logging enabled.")
        except Exception as e:
            logger.warning(f"CloudWatch logging not enabled: {e}")

    #  DynamoDB Initialization 
    with app.app_context():
        try:
            init_tables()
            logger.info("DynamoDB connected and tables initialized.")
        except Exception as e:
            logger.error(f"DynamoDB init error: {e}")

    #  Register Blueprints 
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(subscription_bp)

    logger.info("HomeMade Pickles & Snacks app started successfully.")
    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=settings.DEBUG,
    )
