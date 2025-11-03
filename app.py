from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
import csv
from io import StringIO
import cloudinary
import cloudinary.uploader

# Database and Cloudinary Initialization
db = SQLAlchemy()

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

# ... (rest of your models) ...

# --- Application Factory Function ---
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///eduverse.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)

    cloudinary.config(
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key = os.environ.get('CLOUDINARY_API_KEY'),
        api_secret = os.environ.get('CLOUDINARY_API_SECRET')
    )

    with app.app_context():
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

        # --- Main Routes ---

        @app.route('/')
        def index():
            return render_template('index.html')

        # ... (all your other routes) ...

        # --- Database Initialization Command ---
        @app.cli.command("init-db")
        def init_db_command():
            """Creates the database tables and the initial admin user."""
            db.create_all()
            print("Database tables created!")
            if not User.query.filter_by(role='admin').first():
                admin_user = User(username='admin@miccollege.com', role='admin')
                admin_user.password_hash = generate_password_hash('adminpass')
                db.session.add(admin_user)
                db.session.commit()
                print("Initial admin user created: admin@miccollege.com")
            else:
                print("Admin user already exists.")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)
