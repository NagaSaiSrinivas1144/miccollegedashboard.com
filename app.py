from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
import csv
from io import StringIO
import cloudinary
import cloudinary.uploader

# App Initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///eduverse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

# ... (rest of your models) ...

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

# --- Student Routes ---
@app.route('/student/profile', methods=['GET', 'POST'])
@student_required
def profile():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    if request.method == 'POST':
        if 'profile_pic' in request.files:
            file_to_upload = request.files['profile_pic']
            if file_to_upload:
                try:
                    upload_result = cloudinary.uploader.upload(file_to_upload)
                    student.profile_pic_url = upload_result['secure_url']
                    db.session.commit()
                    flash('Profile picture updated successfully.')
                except Exception as e:
                    flash(f'Error uploading image: {e}', 'error')
                return redirect(url_for('profile'))
    return render_template('student/profile.html', student=student)

# ... (rest of your student routes) ...

# --- Admin Routes ---
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    student = None
    if user.role == 'student':
        student = Student.query.filter_by(user_id=user.id).first()

    if request.method == 'POST':
        user.username = request.form['username']
        user.role = request.form['role']
        if request.form['password']:
            user.set_password(request.form['password'])
        
        if user.role == 'student' and student:
            student.name = request.form.get('name')
            student.email = request.form.get('username') # Keep email in sync with username
            student.department = request.form.get('department')
            student.semester = request.form.get('semester')
            
            if 'profile_pic' in request.files:
                file_to_upload = request.files['profile_pic']
                if file_to_upload:
                    try:
                        upload_result = cloudinary.uploader.upload(file_to_upload)
                        student.profile_pic_url = upload_result['secure_url']
                    except Exception as e:
                        flash(f'Error uploading image: {e}', 'error')

        elif user.role != 'student' and student: # If role changed from student, delete student profile
            db.session.delete(student)

        db.session.commit()
        flash(f'{user.role.capitalize()} {user.username} updated successfully.')
        return redirect(url_for('manage_users'))

    return render_template('admin/edit_user.html', user=user, student=student)

# ... (rest of your admin routes) ...

# --- Teacher Routes ---
@app.route('/teacher/students')
@teacher_required
def teacher_manage_students():
    students = Student.query.all()
    return render_template('teacher/manage_students.html', students=students)

# ... (all your other teacher routes) ...

if __name__ == '__main__':
    app.run(debug=False)
