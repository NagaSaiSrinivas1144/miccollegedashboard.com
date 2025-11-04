from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
import cloudinary
import cloudinary.uploader

# App Initialization
app = Flask(__name__)
@app.route("/")
def home():
    return render_template("index.html")

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///eduverse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- IMPORTANT Render PostgreSQL fix ---
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)

db = SQLAlchemy(app)

# Cloudinary Configuration
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    profile_pic_url = db.Column(db.String(255), nullable=True, default='https://res.cloudinary.com/demo/image/upload/w_150,h_150,c_thumb,g_face,r_max/default.jpg')

# ... ALL YOUR OTHER MODELS HERE (NO CHANGES) ...


# --- Decorators ---
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'student':
            flash('You do not have permission to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'admin':
            flash('You do not have permission to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'teacher':
            flash('You do not have permission to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---- all your routes stay same until manage_users ----

@app.route('/admin/users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

# --- FIX ADDED ROUTE (this was missing) ---
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    student = Student.query.filter_by(user_id=user.id).first()
    if student:
        db.session.delete(student)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully")
    return redirect(url_for('manage_users'))


# ---- rest of your routes remain SAME ----


# --- Database Initialization Command ---
@app.cli.command("init-db")
def init_db_command():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        admin_user = User(username='admin@miccollege.com', role='admin')
        admin_user.password_hash = generate_password_hash('adminpass')
        db.session.add(admin_user)
        db.session.commit()
        print("Initial admin created")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=False)
