
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import User
from app.extensions import db, login_manager
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from flask import abort

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index.index'))
        else:
            flash('用户名或密码错误')
    return render_template('dev/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index.index'))

def admin_required(f):
    """
    A decorator to ensure a user is logged in and is an administrator.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function