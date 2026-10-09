import re
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse
import os
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, abort)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
# To tell where the logged-out users get sent to.
login_manager.login_view = 'login'
# For matching flash categories.
login_manager.login_message_category = 'danger'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.String(30), nullable=False, unique=True)
    age = db.Column(db.Integer, nullable=True)
    department = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Student {self.id}: {self.name}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='staff')   # To specify 'admin' or 'staff'.

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
with app.app_context():
    db.create_all()
@login_manager.user_loader
def load_user(user_id):
    # Flask-Login calls this on every request to turn the session id back into a User
    return db.session.get(User, int(user_id))


def admin_required(view):
    # always put this *under* @login_required so we know someone is logged in
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapper
def is_safe_redirect(target):
    return (bool(target) and target.startswith('/') and '\\' not in target
            and not urlparse(target).netloc)


EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
def validate_student_form(form, student_id=None):
    errors = []

    name = form.get('name', '').strip()
    roll_number = form.get('roll_number', '').strip()
    age_text = form.get('age', '').strip()
    department = form.get('department', '').strip()
    email = form.get('email', '').strip()

    if not name:
        errors.append('Name is required.')
    elif len(name) > 120:
        errors.append('Name must be 120 characters or fewer.')

    if not roll_number:
        errors.append('Roll No is required.')
    elif len(roll_number) > 30:
        errors.append('Roll No must be 30 characters or fewer.')
    else:
        existing = Student.query.filter_by(roll_number=roll_number).first()
        if existing and existing.id != student_id:
            errors.append(f'Roll No "{roll_number}" is already being used by another student.')

    age = None
    if age_text:
        if not age_text.isdecimal() or len(age_text) > 3 or not 5 <= int(age_text) <= 100:
            errors.append('Age must be a whole number between 5 and 100.')
        else:
            age = int(age_text)

    if len(department) > 80:
        errors.append('Department must be 80 characters or fewer.')

    if email and (len(email) > 120 or not EMAIL_PATTERN.match(email)):
        errors.append('Please enter a valid email address.')

    cleaned = {'name': name, 'roll_number': roll_number, 'age': age,
               'department': department, 'email': email}
    return cleaned, errors
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        errors = []
        if not 3 <= len(username) <= 50:
            errors.append('Username must be 3 to 50 characters.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if not errors and User.query.filter_by(username=username).first():
            errors.append('That username is already taken.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html', username=username)

        user = User(username=username)
        user.set_password(password)
        # the very first account becomes the admin, everyone after is staff
        user.role = 'admin' if User.query.count() == 0 else 'staff'
        db.session.add(user)
        db.session.commit()
        flash('Account created. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', username='')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Wrong username or password.', 'danger')
            return render_template('login.html', username=username)
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page if is_safe_redirect(next_page) else url_for('index'))
    return render_template('login.html', username='')
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
SORT_COLUMNS = {
    'name': Student.name,
    'roll_number': Student.roll_number,
    'age': Student.age,
    'department': Student.department,
    'created_at': Student.created_at,
}


@app.template_global()
def url_with(**changes):
    args = request.args.to_dict()
    args.update(changes)
    return url_for(request.endpoint, **args)


@app.route('/')
@login_required
def index():
    q = request.args.get('q', '').strip()
    department = request.args.get('department', '').strip()
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    if sort not in SORT_COLUMNS:
        sort = 'created_at'
    if order not in ('asc', 'desc'):
        order = 'desc'
    per_page = max(1, min(per_page, 50))
    page = max(1, page)

    query = Student.query
    if q:
        like = f'%{q}%'
        query = query.filter(or_(Student.name.ilike(like),
                                 Student.roll_number.ilike(like),
                                 Student.email.ilike(like)))
    if department:
        query = query.filter(Student.department == department)
    column = SORT_COLUMNS[sort]
    column = column.asc() if order == 'asc' else column.desc()
    query = query.order_by(column, Student.id)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    departments = [d[0] for d in db.session.query(Student.department)
    .filter(Student.department.isnot(None), Student.department != '')
    .distinct().order_by(Student.department)]

    return render_template('index.html', students=pagination.items,
                           pagination=pagination, departments=departments,
                           q=q, department=department, sort=sort, order=order)

@app.route('/add', methods=['GET', 'POST'])
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        data, errors = validate_student_form(request.form)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('add.html', form=request.form)

        db.session.add(Student(**data))
        try:
            db.session.commit()
        except IntegrityError:
            # two people saving the same roll no at the same moment
            db.session.rollback()
            flash(f'Roll No "{data["roll_number"]}" already exists.', 'danger')
            return render_template('add.html', form=request.form)

        flash('Student added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add.html', form={})


@app.route('/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        data, errors = validate_student_form(request.form, student_id=student.id)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('edit.html', student=student, form=request.form)

        for field, value in data.items():
            setattr(student, field, value)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(f'Roll No "{data["roll_number"]}" already exists.', 'danger')
            return render_template('edit.html', student=student, form=request.form)

        flash('Student updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', student=student, form={})
@app.route('/delete/<int:student_id>', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student record deleted.', 'info')
    return redirect(url_for('index'))
@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403,
                           message="You don't have permission to do that."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404,
                           message="That page or record doesn't exist."), 404


@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('error.html', code=500,
                           message="Something went wrong on our side."), 500
if __name__ == '__main__':
    app.run(debug=True)