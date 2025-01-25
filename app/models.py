# flask-app/app/models.py
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    """User model for authentication and role management."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'hod', 'exam_officer', 'lecturer', 'admin'
    department = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    otp = db.Column(db.String(6), nullable=True)  # Store OTP  
    otp_expiry = db.Column(db.DateTime, nullable=True)  # Store expiry time for OTP

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

class TokenBlacklist(db.Model):
    """Model for storing blacklisted JWT tokens"""
    __tablename__ = 'token_blacklist'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True)  # JWT ID
    token_type = db.Column(db.String(10), nullable=False)  # 'access' or 'refresh'
    user_id = db.Column(db.Integer, nullable=True)  # Optional: Associate with a user
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<TokenBlacklist jti={self.jti} revoked_at={self.revoked_at}>"

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
    """Result metadata model."""
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'), nullable=False)

    original_file = db.Column(db.String(200), nullable=True)
    upload_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Track when the result was last updated
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Track the lecturer who uploaded the result
    uploader_lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploader = db.relationship('User', foreign_keys=[uploader_lecturer_id], backref=db.backref('uploaded_results', lazy=True))

    course = db.relationship('Course', backref=db.backref('results', lazy=True))
    semester = db.relationship('Semester', backref=db.backref('results', lazy=True))

    def __repr__(self):
        return f"<Result Course={self.course.title}, Semester={self.semester.name}>"


class Score(db.Model):
    """Score details for individual students."""
    __tablename__ = 'scores'

    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('results.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    continuous_assessment = db.Column(db.Float, nullable=False)
    exam_score = db.Column(db.Float, nullable=False)
    total_score = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(2), nullable=False)

    result = db.relationship('Result', backref=db.backref('scores', lazy=True))
    student = db.relationship('Student', backref=db.backref('scores', lazy=True))

    def __repr__(self):
        return f"<Score ResultID={self.result_id}, Student={self.student.name}, Grade={self.grade}>"


class ActionLog(db.Model):
    """Logs all significant actions performed on the system, including result changes."""
    __tablename__ = 'action_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # User performing the action
    action = db.Column(db.String(100), nullable=False)  # Action performed (e.g., 'update_result')
    resource = db.Column(db.String(100), nullable=True)  # Resource affected (e.g., 'Result')
    resource_id = db.Column(db.Integer, nullable=True)  # ID of the resource affected
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Action timestamp
    details = db.Column(db.Text, nullable=True)  # JSON string with details about the action
    ip_address = db.Column(db.String(45), nullable=True)  # IP address of the user
    user_agent = db.Column(db.String(200), nullable=True)  # User agent of the request

    user = db.relationship('User', backref=db.backref('action_logs', lazy=True))

    def __repr__(self):
        return f"<ActionLog {self.action} by User {self.user_id} on {self.resource} ({self.resource_id})>"
