
from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import User
from extensions import db
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from flask import abort

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()

# 这个函数必须在 app 创建时被调用
def init_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # 如果未登录用户访问受保护页面，将重定向到这里

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
            return redirect(url_for('index.index')) # 登录后跳转到后台首页
        else:
            flash('用户名或密码错误')
    return render_template('login.html') # 你需要创建一个简单的 login.html 模板

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index.index')) # 登出后跳转到公共榜单

def admin_required(f):
    """
    A decorator to ensure a user is logged in and is an administrator.
    """
    # @wraps(f) 是一个关键部分，它能保留被装饰函数的元信息（如函数名），
    # 这对于调试和 Flask 的内部工作非常重要。
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查用户是否已认证并且是管理员
        if not current_user.is_authenticated or not current_user.is_admin:
            # 如果检查失败，中止请求并返回 403 Forbidden 错误。
            # 这是一个比重定向到登录页更明确的权限错误。
            abort(403)
        # 如果检查通过，则正常执行原始的路由函数
        return f(*args, **kwargs)
    return decorated_function