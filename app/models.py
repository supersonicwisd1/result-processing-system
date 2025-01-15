# flask-app/app/models.py
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    """User model for authentication and role management."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'hod', 'exam_officer', 'lecturer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

# Many-to-Many relationship table between Courses and Lecturers
course_lecturers = db.Table('course_lecturers',
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
)

class Student(db.Model):
    """Student model for managing student information."""
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Student {self.name} ({self.registration_number})>"

class Course(db.Model):
    """Course model for managing course information."""
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(3), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lecturers = db.relationship('User', secondary=course_lecturers, backref=db.backref('courses', lazy='dynamic'))

    def __repr__(self):
        return f"<Course {self.code} - {self.title}>"

class Semester(db.Model):
    """Semester model for managing semester information."""
    __tablename__ = 'semesters'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Semester {self.name}>"

class Result(db.Model):
    """Result model for managing student results."""
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'), nullable=False)
    
    continuous_assessment = db.Column(db.Float, nullable=False)
    exam_score = db.Column(db.Float, nullable=False)
    total_score = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(2), nullable=False)

    original_file = db.Column(db.String(200), nullable=True)
    upload_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Track when the result was last updated
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Track the lecturer who uploaded the result
    uploader_lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploader = db.relationship('User', foreign_keys=[uploader_lecturer_id], backref=db.backref('uploaded_results', lazy=True))

    student = db.relationship('Student', backref=db.backref('results', lazy=True))
    course = db.relationship('Course', backref=db.backref('results', lazy=True))
    semester = db.relationship('Semester', backref=db.backref('results', lazy=True))

    def __repr__(self):
        return f"<Result {self.student.name} - {self.course.title} - {self.semester.name} : {self.grade}>"
