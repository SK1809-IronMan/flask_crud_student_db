from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


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


with app.app_context():
    db.create_all()
@app.route('/')
def index():
    students = Student.query.order_by(Student.created_at.desc()).all()
    return render_template('index.html', students=students)
@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        age = request.form.get('age', '').strip()
        department = request.form.get('department', '').strip()
        email = request.form.get('email', '').strip()

        if not name or not roll_number:
            flash('Name and Roll No are required.', 'danger')
            return redirect(url_for('add_student'))

        if Student.query.filter_by(roll_number=roll_number).first():
            flash(f'Roll No "{roll_number}" already exists.', 'danger')
            return redirect(url_for('add_student'))

        new_student = Student(
            name=name,
            roll_number=roll_number,
            age=int(age) if age.isdigit() else None,
            department=department,
            email=email
        )
        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add.html')
@app.route('/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()

        if not name or not roll_number:
            flash('Name and Roll No are required.', 'danger')
            return redirect(url_for('edit_student', student_id=student_id))

        existing = Student.query.filter_by(roll_number=roll_number).first()
        if existing and existing.id != student.id:
            flash(f'Roll No "{roll_number}" already used by another student.', 'danger')
            return redirect(url_for('edit_student', student_id=student_id))

        student.name = name
        student.roll_number = roll_number
        age = request.form.get('age', '').strip()
        student.age = int(age) if age.isdigit() else None
        student.department = request.form.get('department', '').strip()
        student.email = request.form.get('email', '').strip()

        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', student=student)
@app.route('/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student record deleted.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)