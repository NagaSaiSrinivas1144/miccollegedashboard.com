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

class InternalMark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    mid_exam1 = db.Column(db.Integer, nullable=False)
    mid_exam2 = db.Column(db.Integer, nullable=False)
    final_mid_exam = db.Column(db.Integer, nullable=False)
    lab_internal = db.Column(db.Integer, nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False)

class AdmissionInquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    course = db.Column(db.String(100), nullable=False)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

class Homework(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.String(20), nullable=False)

class Remark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    remark = db.Column(db.Text, nullable=False)

class TimeTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)
    period1 = db.Column(db.String(50))
    period2 = db.Column(db.String(50))
    period3 = db.Column(db.String(50))

class Fee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)

class AcademicReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    report_url = db.Column(db.String(200), nullable=False)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

class LeaveApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)

class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(100), nullable=False)

class StudentAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    achievement = db.Column(db.Text, nullable=False)

class Download(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    file_url = db.Column(db.String(200), nullable=False)

class AcademicSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(20), nullable=False)

class BookSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

class UniformSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

class ExamFee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)

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

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/student-life')
def student_life():
    return render_template('student_life.html')

@app.route('/facilities')
def facilities():
    return render_template('facilities.html')

@app.route('/uniforms')
def uniforms():
    return render_template('uniforms.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/achievements')
def achievements():
    return render_template('achievements.html')

@app.route('/careers')
def careers():
    return render_template('careers.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/admissions', methods=['GET', 'POST'])
def admissions():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        course = request.form['course']
        inquiry = AdmissionInquiry(name=name, email=email, phone=phone, course=course)
        db.session.add(inquiry)
        db.session.commit()
        flash('Your admission inquiry has been submitted.')
        return redirect(url_for('admissions'))
    return render_template('admissions.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        contact_message = ContactMessage(name=name, email=email, message=message)
        db.session.add(contact_message)
        db.session.commit()
        flash('Thank you for your message. We will get back to you shortly.')
        return redirect(url_for('contact'))
    return render_template('contact.html')

# --- Auth & Dashboard ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = 'student'

        if User.query.filter_by(username=username).first():
            flash('An account with this email already exists.')
            return redirect(url_for('register'))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        new_student = Student(
            name=request.form.get('name'),
            email=username,
            department=request.form.get('department'),
            semester=request.form.get('semester'),
            user_id=new_user.id
        )
        db.session.add(new_student)
        db.session.commit()

        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session['user_role']
    if role == 'admin':
        return render_template('admin/admin_dashboard.html')
    elif role == 'teacher':
        return render_template('teacher/teacher_dashboard.html')
    else:
        return render_template('student/student_dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

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

# --- Admin Routes ---
@app.route('/admin/users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    student = Student.query.filter_by(user_id=user.id).first() if user.role == 'student' else None

    if request.method == 'POST':
        user.username = request.form['username']
        user.role = request.form['role']
        if request.form.get('password'):
            user.set_password(request.form['password'])
        
        if user.role == 'student':
            if not student:
                student = Student(user_id=user.id, email=user.username)
                db.session.add(student)
            student.name = request.form.get('name')
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

        elif user.role != 'student' and student:
            db.session.delete(student)

        db.session.commit()
        flash(f'{user.role.capitalize()} {user.username} updated successfully.')
        return redirect(url_for('manage_users'))

    return render_template('admin/edit_user.html', user=user, student=student)

@app.route('/admin/announcements')
@admin_required
def admin_announcement():
    announcements = Announcement.query.all()
    return render_template('admin/manage_announcements.html', announcements=announcements)

@app.route('/admin/academic_reports')
@admin_required
def admin_academic_reports():
    reports = AcademicReport.query.all()
    return render_template('admin/manage_academic_reports.html', reports=reports)

@app.route('/admin/exam_fees')
@admin_required
def admin_exam_fees():
    exam_fees = ExamFee.query.all()
    return render_template('admin/manage_exam_fees.html', exam_fees=exam_fees)

@app.route('/admin/homework')
@admin_required
def admin_homework():
    homeworks = Homework.query.all()
    return render_template('admin/manage_homework.html', homeworks=homeworks)

@app.route('/admin/remarks')
@admin_required
def admin_remarks():
    remarks = Remark.query.all()
    return render_template('admin/manage_remarks.html', remarks=remarks)

@app.route('/admin/time_table')
@admin_required
def admin_time_table():
    timetables = TimeTable.query.all()
    return render_template('admin/manage_time_table.html', timetables=timetables)

@app.route('/admin/fees')
@admin_required
def admin_fees():
    fees = Fee.query.all()
    return render_template('admin/manage_fees.html', fees=fees)

@app.route('/admin/leave_applications')
@admin_required
def admin_leave_applications():
    leave_applications = LeaveApplication.query.all()
    return render_template('admin/manage_leave_applications.html', leave_applications=leave_applications)

# --- Teacher Routes ---
@app.route('/teacher/students')
@teacher_required
def teacher_manage_students():
    students = Student.query.all()
    return render_template('teacher/manage_students.html', students=students)

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
        print('Admin user already exists.')

if __name__ == '__main__':
    app.run(debug=False)
