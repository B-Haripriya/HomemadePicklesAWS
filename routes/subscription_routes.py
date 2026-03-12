"""
routes/subscription_routes.py
Subscription plan selection and management for customers.
"""

import logging
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash)
from services.subscription_service import (create_subscription,
                                           get_subscriptions_by_user,
                                           update_subscription_status)
from functools import wraps
import config.settings as settings

logger = logging.getLogger(__name__)
subscription_bp = Blueprint('subscription', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@subscription_bp.route('/subscriptions')
def plans():
    """Public page showing available subscription plans."""
    return render_template('subscription/plans.html',
                           plans=settings.SUBSCRIPTION_PLANS)


@subscription_bp.route('/subscriptions/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe():
    if request.method == 'POST':
        plan_key = request.form.get('plan')
        address  = request.form.get('address', '').strip()

        if not address:
            flash('Please provide a delivery address.', 'danger')
            return render_template('subscription/subscribe.html',
                                   plans=settings.SUBSCRIPTION_PLANS,
                                   selected=plan_key)

        result = create_subscription(session['user_id'], plan_key, address)
        if result['success']:
            flash(f"🎉 Subscription activated! Your first box arrives soon.", 'success')
            return redirect(url_for('subscription.my_subscriptions'))
        else:
            flash(result['error'], 'danger')

    plan_key = request.args.get('plan', 'weekly')
    return render_template('subscription/subscribe.html',
                           plans=settings.SUBSCRIPTION_PLANS,
                           selected=plan_key)


@subscription_bp.route('/subscriptions/my')
@login_required
def my_subscriptions():
    subs = get_subscriptions_by_user(session['user_id'])
    return render_template('subscription/my_subscriptions.html', subscriptions=subs)


@subscription_bp.route('/subscriptions/<sub_id>/cancel', methods=['POST'])
@login_required
def cancel_subscription(sub_id):
    from services.subscription_service import get_subscription_by_id
    sub = get_subscription_by_id(sub_id)
    if sub and sub.get('user_id') == session['user_id']:
        update_subscription_status(sub_id, 'cancelled')
        flash('Subscription cancelled.', 'info')
    else:
        flash('Subscription not found.', 'danger')
    return redirect(url_for('subscription.my_subscriptions'))
