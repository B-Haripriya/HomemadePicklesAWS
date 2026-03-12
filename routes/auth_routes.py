"""
routes/auth_routes.py
User registration, login, logout, and profile endpoints.
"""

import logging
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash)
from services.user_service import register_user, login_user, get_user_by_id

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


def _login_required(f):
    """Decorator: redirect to login if user is not authenticated."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('product.home'))

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        phone    = request.form.get('phone', '').strip()

        if not all([name, email, password, confirm]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('auth/register.html')

        result = register_user(name, email, password, phone)
        if result['success']:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result['error'], 'danger')

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('product.home'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = login_user(email, password)
        if user:
            session.permanent = True
            session['user_id']   = user['user_id']
            session['user_name'] = user['name']
            session['user_role'] = user.get('role', 'customer')
            flash(f"Welcome back, {user['name']}! 🥒", 'success')
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            if user.get('role') == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('product.home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@_login_required
def profile():
    user = get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    return render_template('auth/profile.html', user=user)
