from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
import csv
from io import StringIO

# App Initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eduverse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
        role = 'student' # Fixed to student

        if User.query.filter_by(username=username).first():
            flash('An account with this email already exists.')
            return redirect(url_for('register'))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)

        name = request.form.get('name')
        department = request.form.get('department')
        semester = request.form.get('semester')
        
        if not all([name, department, semester]):
            flash('Please fill out all fields for the student profile.')
            db.session.rollback() 
            return redirect(url_for('register'))

        db.session.commit()
        
        new_student = Student(
            name=name,
            email=username,
            department=department,
            semester=semester,
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
@app.route('/student/homework')
@student_required
def homework():
    homeworks = Homework.query.all()
    return render_template('student/homework.html', homeworks=homeworks)

@app.route('/student/remarks')
@student_required
def remarks():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    student_remarks = Remark.query.filter_by(student_id=student.id).all()
    return render_template('student/remarks.html', remarks=student_remarks)

@app.route('/student/time-table')
@student_required
def time_table():
    timetables = TimeTable.query.all()
    return render_template('student/time_table.html', timetables=timetables)

@app.route('/student/fees')
@student_required
def fees():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    student_fees = Fee.query.filter_by(student_id=student.id).all()
    return render_template('student/fees.html', fees=student_fees)

@app.route('/student/profile')
@student_required
def profile():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    return render_template('student/profile.html', student=student)

@app.route('/student/academic-reports')
@student_required
def academic_reports():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    reports = AcademicReport.query.filter_by(student_id=student.id).all()
    return render_template('student/academic_reports.html', reports=reports)

@app.route('/student/announcement')
@student_required
def announcement():
    announcements = Announcement.query.all()
    return render_template('student/announcement.html', announcements=announcements)

@app.route('/student/leave-application', methods=['GET', 'POST'])
@student_required
def leave_application():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    if request.method == 'POST':
        reason = request.form['reason']
        leave = LeaveApplication(student_id=student.id, reason=reason)
        db.session.add(leave)
        db.session.commit()
        flash('Your leave application has been submitted.')
        return redirect(url_for('leave_application'))
    leaves = LeaveApplication.query.filter_by(student_id=student.id).all()
    return render_template('student/leave_application.html', leaves=leaves)

@app.route('/student/payment-list')
@student_required
def payment_list():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    payments = Payment.query.filter_by(student_id=student.id).all()
    return render_template('student/payment_list.html', payments=payments)

@app.route('/student/holiday')
@student_required
def holiday():
    holidays = Holiday.query.all()
    return render_template('student/holiday.html', holidays=holidays)

@app.route('/student/my-achievements')
@student_required
def my_achievements():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    achievements = StudentAchievement.query.filter_by(student_id=student.id).all()
    return render_template('student/my_achievements.html', achievements=achievements)

@app.route('/student/download-list')
@student_required
def download_list():
    downloads = Download.query.all()
    return render_template('student/download_list.html', downloads=downloads)

@app.route('/student/attendance')
@student_required
def student_attendance():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    attendance = Attendance.query.filter_by(student_id=student.id).all()
    return render_template('student/attendance.html', attendance=attendance)

@app.route('/student/academic-schedule')
@student_required
def academic_schedule():
    academic_schedules = AcademicSchedule.query.all()
    return render_template('student/academic_schedule.html', academic_schedules=academic_schedules)

@app.route('/student/book-sales')
@student_required
def book_sales():
    sales = BookSale.query.all()
    return render_template('student/book_sales.html', sales=sales)

@app.route('/student/uniform-sales')
@student_required
def uniform_sales():
    sales = UniformSale.query.all()
    return render_template('student/uniform_sales.html', sales=sales)

@app.route('/student/exam-results')
@student_required
def exam_results():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    internal_marks = InternalMark.query.filter_by(student_id=student.id).all()
    return render_template('student/exam_results.html', internal_marks=internal_marks)

@app.route('/student/pay-exam-fees')
@student_required
def pay_exam_fees():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    exam_fees = ExamFee.query.filter_by(student_id=student.id).all()
    return render_template('student/pay_exam_fees.html', exam_fees=exam_fees)

# --- Admin Routes ---
@app.route('/admin/users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('add_user'))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        if role == 'student':
            name = request.form.get('name')
            department = request.form.get('department')
            semester = request.form.get('semester')
            if not all([name, department, semester]):
                flash('Please fill out all student details.')
                db.session.rollback()
                db.session.delete(new_user) # Delete the user if student details are incomplete
                db.session.commit()
                return redirect(url_for('add_user'))
            new_student = Student(name=name, email=username, department=department, semester=semester, user_id=new_user.id)
            db.session.add(new_student)
            db.session.commit()

        flash(f'{role.capitalize()} {username} added successfully.')
        return redirect(url_for('manage_users'))
    return render_template('admin/add_user.html')

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
        elif user.role != 'student' and student: # If role changed from student, delete student profile
            db.session.delete(student)

        db.session.commit()
        flash(f'{user.role.capitalize()} {user.username} updated successfully.')
        return redirect(url_for('manage_users'))

    return render_template('admin/edit_user.html', user=user, student=student)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin' and User.query.filter_by(role='admin').count() == 1:
        flash('Cannot delete the last admin user.')
        return redirect(url_for('manage_users'))

    if user.role == 'student':
        student = Student.query.filter_by(user_id=user.id).first()
        if student:
            db.session.delete(student)

    db.session.delete(user)
    db.session.commit()
    flash(f'{user.role.capitalize()} {user.username} deleted successfully.')
    return redirect(url_for('manage_users'))

# --- Admin Student Management Routes (Existing, but now distinct from general user management) ---
# Note: The previous /admin/students, /admin/add_student, /admin/edit_student, /admin/delete_student
# routes are now redundant if all user management is done via /admin/users. 
# I will keep them for now, but they could be removed or repurposed if desired.

@app.route('/admin/students')
@admin_required
def manage_students():
    students = Student.query.all()
    return render_template('admin/manage_students.html', students=students)

@app.route('/admin/add_student', methods=['GET', 'POST'])
@admin_required
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        semester = request.form['semester']
        password = request.form['password']

        user = User.query.filter_by(username=email).first()
        if user:
            flash('A user with this email already exists.')
            return redirect(url_for('add_student'))

        new_user = User(username=email, role='student')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        new_student = Student(name=name, email=email, department=department, semester=semester, user_id=new_user.id)
        db.session.add(new_student)
        db.session.commit()

        flash('Student added successfully.')
        return redirect(url_for('manage_students'))
    return render_template('admin/add_student.html')

@app.route('/admin/edit_student/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form['name']
        student.email = request.form['email']
        student.department = request.form['department']
        student.semester = request.form['semester']
        db.session.commit()
        flash('Student details updated.')
        return redirect(url_for('manage_students'))
    return render_template('admin/edit_student.html', student=student)

@app.route('/admin/delete_student/<int:student_id>', methods=['POST'])
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    db.session.delete(student)
    db.session.delete(user)
    db.session.commit()
    flash('Student deleted successfully.')
    return redirect(url_for('manage_students'))

# Admin Homework Routes
@app.route('/admin/homework')
@admin_required
def admin_homework():
    homeworks = Homework.query.all()
    return render_template('admin/manage_homework.html', homeworks=homeworks)

@app.route('/admin/add_homework', methods=['GET', 'POST'])
@admin_required
def add_homework():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        new_homework = Homework(title=title, description=description, due_date=due_date)
        db.session.add(new_homework)
        db.session.commit()
        flash('Homework added successfully.')
        return redirect(url_for('admin_homework'))
    return render_template('admin/add_homework.html')

@app.route('/admin/edit_homework/<int:homework_id>', methods=['GET', 'POST'])
@admin_required
def edit_homework(homework_id):
    homework = Homework.query.get_or_404(homework_id)
    if request.method == 'POST':
        homework.title = request.form['title']
        homework.description = request.form['description']
        homework.due_date = request.form['due_date']
        db.session.commit()
        flash('Homework updated successfully.')
        return redirect(url_for('admin_homework'))
    return render_template('admin/edit_homework.html', homework=homework)

@app.route('/admin/delete_homework/<int:homework_id>', methods=['POST'])
@admin_required
def delete_homework(homework_id):
    homework = Homework.query.get_or_404(homework_id)
    db.session.delete(homework)
    db.session.commit()
    flash('Homework deleted successfully.')
    return redirect(url_for('admin_homework'))

# Admin Announcement Routes
@app.route('/admin/announcements')
@admin_required
def admin_announcement():
    announcements = Announcement.query.all()
    return render_template('admin/manage_announcements.html', announcements=announcements)

@app.route('/admin/add_announcement', methods=['GET', 'POST'])
@admin_required
def add_announcement():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_announcement = Announcement(title=title, content=content)
        db.session.add(new_announcement)
        db.session.commit()
        flash('Announcement added successfully.')
        return redirect(url_for('admin_announcement'))
    return render_template('admin/add_announcement.html')

@app.route('/admin/edit_announcement/<int:announcement_id>', methods=['GET', 'POST'])
@admin_required
def edit_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    if request.method == 'POST':
        announcement.title = request.form['title']
        announcement.content = request.form['content']
        db.session.commit()
        flash('Announcement updated successfully.')
        return redirect(url_for('admin_announcement'))
    return render_template('admin/edit_announcement.html', announcement=announcement)

@app.route('/admin/delete_announcement/<int:announcement_id>', methods=['POST'])
@admin_required
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    flash('Announcement deleted successfully.')
    return redirect(url_for('admin_announcement'))

# Admin Remarks Routes
@app.route('/admin/remarks')
@admin_required
def admin_remarks():
    remarks = Remark.query.all()
    students = Student.query.all()
    return render_template('admin/manage_remarks.html', remarks=remarks, students=students)

@app.route('/admin/add_remark', methods=['GET', 'POST'])
@admin_required
def add_remark():
    students = Student.query.all()
    if request.method == 'POST':
        student_id = request.form['student_id']
        remark_content = request.form['remark']
        new_remark = Remark(student_id=student_id, remark=remark_content)
        db.session.add(new_remark)
        db.session.commit()
        flash('Remark added successfully.')
        return redirect(url_for('admin_remarks'))
    return render_template('admin/add_remark.html', students=students)

@app.route('/admin/edit_remark/<int:remark_id>', methods=['GET', 'POST'])
@admin_required
def edit_remark(remark_id):
    remark = Remark.query.get_or_404(remark_id)
    students = Student.query.all()
    if request.method == 'POST':
        remark.student_id = request.form['student_id']
        remark.remark = request.form['remark']
        db.session.commit()
        flash('Remark updated successfully.')
        return redirect(url_for('admin_remarks'))
    return render_template('admin/edit_remark.html', remark=remark, students=students)

@app.route('/admin/delete_remark/<int:remark_id>', methods=['POST'])
@admin_required
def delete_remark(remark_id):
    remark = Remark.query.get_or_404(remark_id)
    db.session.delete(remark)
    db.session.commit()
    flash('Remark deleted successfully.')
    return redirect(url_for('admin_remarks'))

# Admin Time Table Routes
@app.route('/admin/time_table')
@admin_required
def admin_time_table():
    timetables = TimeTable.query.all()
    return render_template('admin/manage_time_table.html', timetables=timetables)

@app.route('/admin/add_time_table', methods=['GET', 'POST'])
@admin_required
def add_time_table():
    if request.method == 'POST':
        day = request.form['day']
        period1 = request.form['period1']
        period2 = request.form['period2']
        period3 = request.form['period3']
        new_time_table = TimeTable(day=day, period1=period1, period2=period2, period3=period3)
        db.session.add(new_time_table)
        db.session.commit()
        flash('Time Table entry added successfully.')
        return redirect(url_for('admin_time_table'))
    return render_template('admin/add_time_table.html')

@app.route('/admin/edit_time_table/<int:time_table_id>', methods=['GET', 'POST'])
@admin_required
def edit_time_table(time_table_id):
    time_table_entry = TimeTable.query.get_or_404(time_table_id)
    if request.method == 'POST':
        time_table_entry.day = request.form['day']
        time_table_entry.period1 = request.form['period1']
        time_table_entry.period2 = request.form['period2']
        time_table_entry.period3 = request.form['period3']
        db.session.commit()
        flash('Time Table entry updated successfully.')
        return redirect(url_for('admin_time_table'))
    return render_template('admin/edit_time_table.html', time_table_entry=time_table_entry)

@app.route('/admin/delete_time_table/<int:time_table_id>', methods=['POST'])
@admin_required
def delete_time_table(time_table_id):
    time_table_entry = TimeTable.query.get_or_404(time_table_id)
    db.session.delete(time_table_entry)
    db.session.commit()
    flash('Time Table entry deleted successfully.')
    return redirect(url_for('admin_time_table'))

# Admin Fees Routes
@app.route('/admin/fees')
@admin_required
def admin_fees():
    fees = Fee.query.all()
    students = Student.query.all()
    return render_template('admin/manage_fees.html', fees=fees, students=students)

@app.route('/admin/add_fee', methods=['GET', 'POST'])
@admin_required
def add_fee():
    students = Student.query.all()
    if request.method == 'POST':
        student_id = request.form['student_id']
        amount = request.form['amount']
        status = request.form['status']
        new_fee = Fee(student_id=student_id, amount=amount, status=status)
        db.session.add(new_fee)
        db.session.commit()
        flash('Fee entry added successfully.')
        return redirect(url_for('admin_fees'))
    return render_template('admin/add_fee.html', students=students)

@app.route('/admin/edit_fee/<int:fee_id>', methods=['GET', 'POST'])
@admin_required
def edit_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    students = Student.query.all()
    if request.method == 'POST':
        fee.student_id = request.form['student_id']
        fee.amount = request.form['amount']
        fee.status = request.form['status']
        db.session.commit()
        flash('Fee entry updated successfully.')
        return redirect(url_for('admin_fees'))
    return render_template('admin/edit_fee.html', fee=fee, students=students)

@app.route('/admin/delete_fee/<int:fee_id>', methods=['POST'])
@admin_required
def delete_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    db.session.delete(fee)
    db.session.commit()
    flash('Fee entry deleted successfully.')
    return redirect(url_for('admin_fees'))

# Admin Academic Reports Routes
@app.route('/admin/academic_reports')
@admin_required
def admin_academic_reports():
    reports = AcademicReport.query.all()
    students = Student.query.all()
    return render_template('admin/manage_academic_reports.html', reports=reports, students=students)

@app.route('/admin/add_academic_report', methods=['GET', 'POST'])
@admin_required
def add_academic_report():
    students = Student.query.all()
    if request.method == 'POST':
        student_id = request.form['student_id']
        report_url = request.form['report_url']
        new_report = AcademicReport(student_id=student_id, report_url=report_url)
        db.session.add(new_report)
        db.session.commit()
        flash('Academic Report added successfully.')
        return redirect(url_for('admin_academic_reports'))
    return render_template('admin/add_academic_report.html', students=students)

@app.route('/admin/edit_academic_report/<int:report_id>', methods=['GET', 'POST'])
@admin_required
def edit_academic_report(report_id):
    report = AcademicReport.query.get_or_404(report_id)
    students = Student.query.all()
    if request.method == 'POST':
        report.student_id = request.form['student_id']
        report.report_url = request.form['report_url']
        db.session.commit()
        flash('Academic Report updated successfully.')
        return redirect(url_for('admin_academic_reports'))
    return render_template('admin/edit_academic_report.html', report=report, students=students)

@app.route('/admin/delete_academic_report/<int:report_id>', methods=['POST'])
@admin_required
def delete_academic_report(report_id):
    report = AcademicReport.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    flash('Academic Report deleted successfully.')
    return redirect(url_for('admin_academic_reports'))

# Admin Leave Application Routes
@app.route('/admin/leave_applications')
@admin_required
def admin_leave_applications():
    leave_applications = LeaveApplication.query.all()
    return render_template('admin/manage_leave_applications.html', leave_applications=leave_applications)

@app.route('/admin/edit_leave_application/<int:leave_id>', methods=['GET', 'POST'])
@admin_required
def edit_leave_application(leave_id):
    leave_application = LeaveApplication.query.get_or_404(leave_id)
    if request.method == 'POST':
        leave_application.status = request.form['status']
        db.session.commit()
        flash('Leave application status updated.')
        return redirect(url_for('admin_leave_applications'))
    return render_template('admin/edit_leave_application.html', leave_application=leave_application)

@app.route('/admin/delete_leave_application/<int:leave_id>', methods=['POST'])
@admin_required
def delete_leave_application(leave_id):
    leave_application = LeaveApplication.query.get_or_404(leave_id)
    db.session.delete(leave_application)
    db.session.commit()
    flash('Leave application deleted.')
    return redirect(url_for('admin_leave_applications'))

# Admin Payments Routes
@app.route('/admin/payments')
@admin_required
def admin_payments():
    payments = Payment.query.all()
    students = Student.query.all()
    return render_template('admin/manage_payments.html', payments=payments, students=students)

@app.route('/admin/add_payment', methods=['GET', 'POST'])
@admin_required
def add_payment():
    students = Student.query.all()
    if request.method == 'POST':
        student_id = request.form['student_id']
        amount = request.form['amount']
        date = request.form['date']
        new_payment = Payment(student_id=student_id, amount=amount, date=date)
        db.session.add(new_payment)
        db.session.commit()
        flash('Payment added successfully.')
        return redirect(url_for('admin_payments'))
    return render_template('admin/add_payment.html', students=students)

@app.route('/admin/edit_payment/<int:payment_id>', methods=['GET', 'POST'])
@admin_required
def edit_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    students = Student.query.all()
    if request.method == 'POST':
        payment.student_id = request.form['student_id']
        payment.amount = request.form['amount']
        payment.date = request.form['date']
        db.session.commit()
        flash('Payment updated successfully.')
        return redirect(url_for('admin_payments'))
    return render_template('admin/edit_payment.html', payment=payment, students=students)

@app.route('/admin/delete_payment/<int:payment_id>', methods=['POST'])
@admin_required
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    db.session.delete(payment)
    db.session.commit()
    flash('Payment deleted successfully.')
    return redirect(url_for('admin_payments'))

# Admin Holidays Routes
@app.route('/admin/holidays')
@admin_required
def admin_holidays():
    holidays = Holiday.query.all()
    return render_template('admin/manage_holidays.html', holidays=holidays)

@app.route('/admin/add_holiday', methods=['GET', 'POST'])
@admin_required
def add_holiday():
    if request.method == 'POST':
        date = request.form['date']
        reason = request.form['reason']
        new_holiday = Holiday(date=date, reason=reason)
        db.session.add(new_holiday)
        db.session.commit()
        flash('Holiday added successfully.')
        return redirect(url_for('admin_holidays'))
    return render_template('admin/add_holiday.html')

@app.route('/admin/edit_holiday/<int:holiday_id>', methods=['GET', 'POST'])
@admin_required
def edit_holiday(holiday_id):
    holiday = Holiday.query.get_or_404(holiday_id)
    if request.method == 'POST':
        holiday.date = request.form['date']
        holiday.reason = request.form['reason']
        db.session.commit()
        flash('Holiday updated successfully.')
        return redirect(url_for('admin_holidays'))
    return render_template('admin/edit_holiday.html', holiday=holiday)

@app.route('/admin/delete_holiday/<int:holiday_id>', methods=['POST'])
@admin_required
def delete_holiday(holiday_id):
    holiday = Holiday.query.get_or_404(holiday_id)
    db.session.delete(holiday)
    db.session.commit()
    flash('Holiday deleted successfully.')
    return redirect(url_for('admin_holidays'))

# Admin Student Achievements Routes
@app.route('/admin/achievements')
@admin_required
def admin_achievements():
    achievements = StudentAchievement.query.all()
    students = Student.query.all()
    return render_template('admin/manage_achievements.html', achievements=achievements, students=students)

@app.route('/admin/add_achievement', methods=['GET', 'POST'])
@admin_required
def add_achievement():
    students = Student.query.all()
    if request.method == 'POST':
        student_id = request.form['student_id']
        achievement_text = request.form['achievement']
        new_achievement = StudentAchievement(student_id=student_id, achievement=achievement_text)
        db.session.add(new_achievement)
        db.session.commit()
        flash('Achievement added successfully.')
        return redirect(url_for('admin_achievements'))
    return render_template('admin/add_achievement.html', students=students)

@app.route('/admin/edit_achievement/<int:achievement_id>', methods=['GET', 'POST'])
@admin_required
def edit_achievement(achievement_id):
    achievement = StudentAchievement.query.get_or_404(achievement_id)
    students = Student.query.all()
    if request.method == 'POST':
        achievement.student_id = request.form['student_id']
        achievement.achievement = request.form['achievement']
        db.session.commit()
        flash('Achievement updated successfully.')
        return redirect(url_for('admin_achievements'))
    return render_template('admin/edit_achievement.html', achievement=achievement, students=students)

@app.route('/admin/delete_achievement/<int:achievement_id>', methods=['POST'])
@admin_required
def delete_achievement(achievement_id):
    achievement = StudentAchievement.query.get_or_404(achievement_id)
    db.session.delete(achievement)
    db.session.commit()
    flash('Achievement deleted successfully.')
    return redirect(url_for('admin_achievements'))

# Admin Downloads Routes
@app.route('/admin/downloads')
@admin_required
def admin_downloads():
    downloads = Download.query.all()
    return render_template('admin/manage_downloads.html', downloads=downloads)

@app.route('/admin/add_download', methods=['GET', 'POST'])
@admin_required
def add_download():
    if request.method == 'POST':
        title = request.form['title']
        file_url = request.form['file_url']
        new_download = Download(title=title, file_url=file_url)
        db.session.add(new_download)
        db.session.commit()
        flash('Download added successfully.')
        return redirect(url_for('admin_downloads'))
    return render_template('admin/add_download.html')

@app.route('/admin/edit_download/<int:download_id>', methods=['GET', 'POST'])
@admin_required
def edit_download(download_id):
    download = Download.query.get_or_404(download_id)
    if request.method == 'POST':
        download.title = request.form['title']
        download.file_url = request.form['file_url']
        db.session.commit()
        flash('Download updated successfully.')
        return redirect(url_for('admin_downloads'))
    return render_template('admin/edit_download.html', download=download)

@app.route('/admin/delete_download/<int:download_id>', methods=['POST'])
@admin_required
def delete_download(download_id):
    download = Download.query.get_or_404(download_id)
    db.session.delete(download)
    db.session.commit()
    flash('Download deleted successfully.')
    return redirect(url_for('admin_downloads'))

# Admin Academic Schedule Routes
@app.route('/admin/academic_schedule')
@admin_required
def admin_academic_schedule():
    academic_schedules = AcademicSchedule.query.all()
    return render_template('admin/manage_academic_schedule.html', academic_schedules=academic_schedules)

@app.route('/admin/add_academic_schedule', methods=['GET', 'POST'])
@admin_required
def add_academic_schedule():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        new_academic_schedule = AcademicSchedule(title=title, description=description, date=date)
        db.session.add(new_academic_schedule)
        db.session.commit()
        flash('Academic Schedule entry added successfully.')
        return redirect(url_for('admin_academic_schedule'))
    return render_template('admin/add_academic_schedule.html')

@app.route('/admin/edit_academic_schedule/<int:schedule_id>', methods=['GET', 'POST'])
@admin_required
def edit_academic_schedule(schedule_id):
    academic_schedule = AcademicSchedule.query.get_or_404(schedule_id)
    if request.method == 'POST':
        academic_schedule.title = request.form['title']
        academic_schedule.description = request.form['description']
        academic_schedule.date = request.form['date']
        db.session.commit()
        flash('Academic Schedule entry updated successfully.')
        return redirect(url_for('admin_academic_schedule'))
    return render_template('admin/edit_academic_schedule.html', academic_schedule=academic_schedule)

@app.route('/admin/delete_academic_schedule/<int:schedule_id>', methods=['POST'])
@admin_required
def delete_academic_schedule(schedule_id):
    academic_schedule = AcademicSchedule.query.get_or_404(schedule_id)
    db.session.delete(academic_schedule)
    db.session.commit()
    flash('Academic Schedule entry deleted successfully.')
    return redirect(url_for('admin_academic_schedule'))

# Admin Book Sales Routes
@app.route('/admin/book_sales')
@admin_required
def admin_book_sales():
    book_sales = BookSale.query.all()
    return render_template('admin/manage_book_sales.html', book_sales=book_sales)

@app.route('/admin/add_book_sale', methods=['GET', 'POST'])
@admin_required
def add_book_sale():
    if request.method == 'POST':
        book_name = request.form['book_name']
        price = request.form['price']
        new_book_sale = BookSale(book_name=book_name, price=price)
        db.session.add(new_book_sale)
        db.session.commit()
        flash('Book sale entry added successfully.')
        return redirect(url_for('admin_book_sales'))
    return render_template('admin/add_book_sale.html')

@app.route('/admin/edit_book_sale/<int:book_sale_id>', methods=['GET', 'POST'])
@admin_required
def edit_book_sale(book_sale_id):
    book_sale = BookSale.query.get_or_404(book_sale_id)
    if request.method == 'POST':
        book_sale.book_name = request.form['book_name']
        book_sale.price = request.form['price']
        db.session.commit()
        flash('Book sale entry updated successfully.')
        return redirect(url_for('admin_book_sales'))
    return render_template('admin/edit_book_sale.html', book_sale=book_sale)

@app.route('/admin/delete_book_sale/<int:book_sale_id>', methods=['POST'])
@admin_required
def delete_book_sale(book_sale_id):
    book_sale = BookSale.query.get_or_404(book_sale_id)
    db.session.delete(book_sale)
    db.session.commit()
    flash('Book sale entry deleted successfully.')
    return redirect(url_for('admin_book_sales'))

# Admin Uniform Sales Routes
@app.route('/admin/uniform_sales')
@admin_required
def admin_uniform_sales():
    uniform_sales = UniformSale.query.all()
    return render_template('admin/manage_uniform_sales.html', uniform_sales=uniform_sales)

@app.route('/admin/add_uniform_sale', methods=['GET', 'POST'])
@admin_required
def add_uniform_sale():
    if request.method == 'POST':
        item = request.form['item']
        price = request.form['price']
        new_uniform_sale = UniformSale(item=item, price=price)
        db.session.add(new_uniform_sale)
        db.session.commit()
        flash('Uniform sale entry added successfully.')
        return redirect(url_for('admin_uniform_sales'))
    return render_template('admin/add_uniform_sale.html')

@app.route('/admin/edit_uniform_sale/<int:uniform_sale_id>', methods=['GET', 'POST'])
@admin_required
def edit_uniform_sale(uniform_sale_id):
    uniform_sale = UniformSale.query.get_or_404(uniform_sale_id)
    if request.method == 'POST':
        uniform_sale.item = request.form['item']
        uniform_sale.price = request.form['price']
        db.session.commit()
        flash('Uniform sale entry updated successfully.')
        return redirect(url_for('admin_uniform_sales'))
    return render_template('admin/edit_uniform_sale.html', uniform_sale=uniform_sale)

@app.route('/admin/delete_uniform_sale/<int:uniform_sale_id>', methods=['POST'])
@admin_required
def delete_uniform_sale(uniform_sale_id):
    uniform_sale = UniformSale.query.get_or_404(uniform_sale_id)
    db.session.delete(uniform_sale)
    db.session.commit()
    flash('Uniform sale entry deleted successfully.')
    return redirect(url_for('admin_uniform_sales'))

# Admin Exam Fees Routes
@app.route('/admin/exam_fees')
@admin_required
def admin_exam_fees():
    exam_fees = ExamFee.query.all()
    students = Student.query.all()
    return render_template('admin/manage_exam_fees.html', exam_fees=exam_fees, students=students)

@app.route('/admin/add_exam_fee', methods=['GET', 'POST'])
@admin_required
def add_exam_fee():
    students = Student.query.all()
    if request.method == 'POST':
        student_id = request.form['student_id']
        amount = request.form['amount']
        status = request.form['status']
        new_exam_fee = ExamFee(student_id=student_id, amount=amount, status=status)
        db.session.add(new_exam_fee)
        db.session.commit()
        flash('Exam fee entry added successfully.')
        return redirect(url_for('admin_exam_fees'))
    return render_template('admin/add_exam_fee.html', students=students)

@app.route('/admin/edit_exam_fee/<int:exam_fee_id>', methods=['GET', 'POST'])
@admin_required
def edit_exam_fee(exam_fee_id):
    exam_fee = ExamFee.query.get_or_404(exam_fee_id)
    students = Student.query.all()
    if request.method == 'POST':
        exam_fee.student_id = request.form['student_id']
        exam_fee.amount = request.form['amount']
        exam_fee.status = request.form['status']
        db.session.commit()
        flash('Exam fee entry updated successfully.')
        return redirect(url_for('admin_exam_fees'))
    return render_template('admin/edit_exam_fee.html', exam_fee=exam_fee, students=students)

@app.route('/admin/delete_exam_fee/<int:exam_fee_id>', methods=['POST'])
@admin_required
def delete_exam_fee(exam_fee_id):
    exam_fee = ExamFee.query.get_or_404(exam_fee_id)
    db.session.delete(exam_fee)
    db.session.commit()
    flash('Exam fee entry deleted successfully.')
    return redirect(url_for('admin_exam_fees'))

# --- Teacher Routes ---
@app.route('/teacher/students')
@teacher_required
def teacher_manage_students():
    students = Student.query.all()
    return render_template('teacher/manage_students.html', students=students)

@app.route('/teacher/student/<int:student_id>/internal_marks', methods=['GET', 'POST'])
@teacher_required
def manage_internal_marks(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        semester = request.form['semester']
        subject = request.form['subject']
        mid_exam1 = request.form['mid_exam1']
        mid_exam2 = request.form['mid_exam2']
        final_mid_exam = request.form['final_mid_exam']
        lab_internal = request.form['lab_internal']
        
        new_internal_mark = InternalMark(student_id=student_id, semester=semester, subject=subject,
                                         mid_exam1=mid_exam1, mid_exam2=mid_exam2,
                                         final_mid_exam=final_mid_exam, lab_internal=lab_internal)
        db.session.add(new_internal_mark)
        db.session.commit()
        flash('Internal Marks added successfully.')
        return redirect(url_for('manage_internal_marks', student_id=student_id))
    
    internal_marks = InternalMark.query.filter_by(student_id=student_id).all()
    return render_template('teacher/manage_internal_marks.html', student=student, internal_marks=internal_marks)

@app.route('/teacher/student/<int:student_id>/internal_marks/add', methods=['GET', 'POST'])
@teacher_required
def add_internal_mark(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        semester = request.form['semester']
        subject = request.form['subject']
        mid_exam1 = request.form['mid_exam1']
        mid_exam2 = request.form['mid_exam2']
        final_mid_exam = request.form['final_mid_exam']
        lab_internal = request.form['lab_internal']
        
        new_internal_mark = InternalMark(student_id=student_id, semester=semester, subject=subject,
                                         mid_exam1=mid_exam1, mid_exam2=mid_exam2,
                                         final_mid_exam=final_mid_exam, lab_internal=lab_internal)
        db.session.add(new_internal_mark)
        db.session.commit()
        flash('Internal Marks added successfully.')
        return redirect(url_for('manage_internal_marks', student_id=student_id))
    return render_template('teacher/add_internal_mark.html', student=student)

@app.route('/teacher/edit_internal_mark/<int:mark_id>', methods=['GET', 'POST'])
@teacher_required
def edit_internal_mark(mark_id):
    internal_mark = InternalMark.query.get_or_404(mark_id)
    student = Student.query.get_or_404(internal_mark.student_id)
    if request.method == 'POST':
        internal_mark.semester = request.form['semester']
        internal_mark.subject = request.form['subject']
        internal_mark.mid_exam1 = request.form['mid_exam1']
        internal_mark.mid_exam2 = request.form['mid_exam2']
        internal_mark.final_mid_exam = request.form['final_mid_exam']
        internal_mark.lab_internal = request.form['lab_internal']
        db.session.commit()
        flash('Internal Mark updated successfully.')
        return redirect(url_for('manage_internal_marks', student_id=internal_mark.student_id))
    return render_template('teacher/edit_internal_mark.html', internal_mark=internal_mark, student=student)

@app.route('/teacher/delete_internal_mark/<int:mark_id>', methods=['POST'])
@teacher_required
def delete_internal_mark(mark_id):
    internal_mark = InternalMark.query.get_or_404(mark_id)
    student_id = internal_mark.student_id
    db.session.delete(internal_mark)
    db.session.commit()
    flash('Internal Mark deleted successfully.')
    return redirect(url_for('manage_internal_marks', student_id=student_id))

@app.route('/download_sample_internal_marks_csv')
@teacher_required
def download_sample_internal_marks_csv():
    sample_csv_content = "student_email,semester,subject,mid_exam1,mid_exam2,final_mid_exam,lab_internal\n"
    sample_csv_content += "student1@example.com,1,Math,80,85,90,15\n"
    sample_csv_content += "student2@example.com,1,Science,75,70,80,12\n"
    
    response = make_response(sample_csv_content)
    response.headers["Content-Disposition"] = "attachment; filename=sample_internal_marks.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/teacher/upload_internal_marks', methods=['GET', 'POST'])
@teacher_required
def upload_internal_marks():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and file.filename.endswith('.csv'):
            stream = StringIO(file.stream.read().decode("UTF8"))
            csv_reader = csv.DictReader(stream)
            updated_count = 0
            errors = []

            for row in csv_reader:
                try:
                    student_email = row['student_email']
                    student = Student.query.filter_by(email=student_email).first()
                    if not student:
                        errors.append(f"Student with email {student_email} not found.")
                        continue

                    # Attempt to find existing mark or create new
                    internal_mark = InternalMark.query.filter_by(
                        student_id=student.id,
                        semester=int(row['semester']),
                        subject=row['subject']
                    ).first()

                    if not internal_mark:
                        internal_mark = InternalMark(student_id=student.id)
                        db.session.add(internal_mark)
                    
                    internal_mark.semester = int(row['semester'])
                    internal_mark.subject = row['subject']
                    internal_mark.mid_exam1 = int(row['mid_exam1'])
                    internal_mark.mid_exam2 = int(row['mid_exam2'])
                    internal_mark.final_mid_exam = int(row['final_mid_exam'])
                    internal_mark.lab_internal = int(row['lab_internal'])
                    updated_count += 1

                except Exception as e:
                    errors.append(f"Error processing row for {row.get('student_email', 'unknown')}: {e}")
                    db.session.rollback()
                    
            db.session.commit()
            if updated_count > 0:
                flash(f'Successfully processed {updated_count} internal mark entries.')
            for error in errors:
                flash(f'Error: {error}', 'error')
            return redirect(url_for('upload_internal_marks'))
        else:
            flash('Invalid file format. Please upload a CSV file.', 'error')
    
    return render_template('teacher/upload_internal_marks.html')

@app.route('/teacher/student/<int:student_id>/attendance', methods=['GET', 'POST'])
@teacher_required
def manage_attendance(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        date = request.form['date']
        status = request.form['status']
        new_attendance = Attendance(student_id=student_id, date=date, status=status)
        db.session.add(new_attendance)
        db.session.commit()
        flash('Attendance recorded.')
        return redirect(url_for('manage_attendance', student_id=student_id))
    
    attendance = Attendance.query.filter_by(student_id=student.id).all()
    return render_template('teacher/manage_attendance.html', student=student, attendance=attendance)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # --- IMPORTANT: Initial Admin Creation --- #
        # If no admin user exists, you can create one manually here for the first run.
        # After the first run, you can comment this out or remove it.
        # Example: 
        # if not User.query.filter_by(role='admin').first():
        #     admin_user = User(username='admin@miccollege.com', role='admin')
        #     admin_user.set_password('adminpass') # Choose a strong password
        #     db.session.add(admin_user)
        #     db.session.commit()
        #     print("Initial admin user created: admin@miccollege.com with password 'adminpass'")
        # ----------------------------------------- #
    app.run(debug=True)
