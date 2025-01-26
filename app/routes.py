# flask-app/app/routes.py
import os
from flask import Blueprint, request, jsonify, session, abort
from flask_jwt_extended import create_access_token, jwt_required as original_jwt_required, get_jwt_identity, get_jwt, decode_token, verify_jwt_in_request
from .utils import (create_error_response, get_user_by_id, get_user_by_username, get_user_by_email,
                    get_student_by_registration, check_required_fields,
                    get_or_create_course, get_or_create_semester, process_result, save_file, save_results_to_db, send_otp_email,
                    process_uploaded_file, process_scores_data)
from .models import User, db, Result, Student, Course, Semester, ActionLog, TokenBlacklist, Score
from .constants import ALLOWED_ROLES, UPLOAD_FOLDER
from functools import wraps
from flask_restx import Api, Resource, fields, Namespace
import json
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import random
import string

import logging

logging.basicConfig(level=logging.DEBUG)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create API blueprint
api_blueprint = Blueprint('api', __name__)


api = Api(
    title='Student Results API',
    version='1.0',
    description='API for managing student results',
    prefix='/api/v1',
    doc='/docs',
    security='Bearer'
)

# Create namespaces
auth_ns = Namespace('auth', description='Authentication operations')
results_ns = Namespace('results', description='Results operations')
course_ns = Namespace('courses', description='Course operations')
student_ns = Namespace('students', description='Student operations')
security_ns = Namespace('security', description='Security operations')

# Add namespaces to API
api.add_namespace(auth_ns)
api.add_namespace(results_ns)
api.add_namespace(course_ns)
api.add_namespace(student_ns)
api.add_namespace(security_ns)

# Models for Swagger documentation
user_model = api.model('User', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password'),
    'email': fields.String(required=True, description='Email'),
    'department': fields.String(required=True, description='Department'),
    'role': fields.String(required=True, description='User role', enum=ALLOWED_ROLES)
})

change_password_model = api.model('ChangePassword', {
    'old_password': fields.String(required=True, description='The current password'),
    'new_password': fields.String(required=True, description='The new password to set')
})

forgot_password_model = api.model('ForgotPassword', {
    'email': fields.String(required=True, description='The email associated with the user account')
})

reset_password_model = api.model('ResetPassword', {
    'email': fields.String(required=True, description='The email associated with the user account'),
    'otp': fields.String(required=True, description='Code sent for password reset'),
    'new_password': fields.String(required=True, description='The new password to set')
})

update_email_model = api.model('UpdateEmail', {
    'new_email': fields.String(required=True, description='The new email address to update')
})

update_username_model = api.model('UpdateUsername', {
    'new_username': fields.String(required=True, description='The new username to set')
})

login_model = api.model('Login', {
    'username': fields.String(required=False, description='Username'),
    'email': fields.String(required=False, description='Email'),
    'password': fields.String(required=True, description='Password')
})

student_result_model = api.model('StudentResult', {
    'registration_number': fields.String(required=True, description='Student registration number'),
    'ca_score': fields.Float(required=True, description='Continuous Assessment score'),
    'exam_score': fields.Float(required=True, description='Examination score'),
    'total_score': fields.Float(required=True, description='Total score'),
    'grade': fields.String(required=True, description='Grade achieved')
})

score_update_model = api.model('ScoreUpdate', {
    'registration_number': fields.String(required=True, description='Student registration number'),
    'ca_score': fields.Float(description='Continuous assessment score'),
    'exam_score': fields.Float(description='Exam score'),
    'total_score': fields.Float(description='Total score'),
    'grade': fields.String(description='Grade achieved')
})

result_update_model = api.model('ResultUpdate', {
    'course_code': fields.String(description='Course code'),
    'course_title': fields.String(description='Course title'),
    'course_unit': fields.Integer(description='Course unit'),
    'semester_name': fields.String(description='Semester name'),
    'session': fields.String(description='Academic session'),
    'department': fields.String(description='Department'),
})


result_model = api.model('Result', {
    'course_code': fields.String(required=True, description='Course code'),
    'course_title': fields.String(required=True, description='Course title'),
    'course_unit': fields.Integer(required=True, description='Course credit units'),
    'level': fields.Integer(required=True, description='Academic level'),
    'faculty': fields.String(required=True, description='Faculty name'),
    'exam_department': fields.String(required=True, description='Examining department'),
    'semester_name': fields.String(required=True, description='Semester name'),
    'session': fields.String(required=True, description='Academic session'),
    'results': fields.List(fields.Nested(student_result_model), required=True, description='List of student results')
})

# Custom JWT required decorator  
# Custom JWT required decorator  
def jwt_required(*args, **kwargs):  
    def wrapper(fn):  
        @wraps(fn)  
        def decorated(*args, **kwargs):  
            # First, verify the JWT in the request  
            try:  
                verify_jwt_in_request(*args, **kwargs)  # This will raise an error if the token is invalid or missing  
            except Exception as e:  
                abort(401, description=str(e))  # Handle the exception and return unauthorized  

            # Now that the token is verified, check if it's blacklisted  
            jti = get_jwt()["jti"]  
            if TokenBlacklist.query.filter_by(jti=jti).scalar() is not None:  
                abort(401, description="Token has been revoked")  # Unauthorized  

            return fn(*args, **kwargs)  # Call the original function  
        return decorated  
    return wrapper  

# Authorization decorator  
def role_required(*roles):  
    def decorator(f):  
        @wraps(f)  
        def decorated_function(*args, **kwargs):  
            current_user_id = get_jwt_identity()  
            current_user = User.query.get(current_user_id)  # Adjust based on your User model  
            if current_user is None or current_user.role not in roles:  
                return {"error": "You are not authorized to access this resource"}, 403  
            return f(*args, **kwargs)  
        return decorated_function  
    return decorator  

# JWT role decorator  
def jwt_role_required(*roles):  
    def wrapper(fn):  
        @wraps(fn)  
        @jwt_required()  # Use the updated jwt_required  
        @role_required(*roles)  
        def decorated(*args, **kwargs):  
            return fn(*args, **kwargs)  
        return decorated  
    return wrapper

# Authentication routes
@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(user_model)
    @auth_ns.response(201, 'User registered successfully')
    @auth_ns.response(400, 'Validation error')
    @auth_ns.doc(description='Register a new user')
    def post(self):
        """Register a new user with the system"""
        data = request.json
        username = data.get('username')
        email = data.get('email')
        department = data.get('department')
        password = data.get('password')
        role = data.get('role')

        if not username or not password or not role:
            return create_error_response("Username, password, and role are required")
        if role not in ALLOWED_ROLES:
            return create_error_response(f"Invalid role. Allowed roles are {', '.join(ALLOWED_ROLES)}")

        existing_user = get_user_by_username(username)
        if existing_user:
            return create_error_response("User with this username already exists")

        new_user = User(username=username, role=role, email=email, department=department)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Log action
        log = ActionLog(
            user_id=None,
            action="register_user",
            resource="User",
            resource_id=new_user.id,
            details=json.dumps({"username": username, 'email': email, "role": role}),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)
        db.session.commit()

        return {"message": "User registered successfully"}, 201

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Login successful')
    @auth_ns.response(401, 'Invalid credentials')
    def post(self):
        """Login the user"""
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if (not username or not email) and not password:
            return {"error": "Username or Email and Password required"}, 400

        user = get_user_by_username(username) if username else get_user_by_email(email)
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.id)

            # Log action
            log = ActionLog(
                user_id=user.id,
                action="login",
                resource="User",
                resource_id=user.id,
                details=json.dumps({"username": user.username}),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(log)
            db.session.commit()

            return {"access_token": access_token, "role": user.role}, 200

        return {"error": "Invalid credentials"}, 401

@auth_ns.route('/logout')  
class Logout(Resource):  
    @jwt_required()  
    def post(self):  
        jti = get_jwt()["jti"]  # JWT ID  
        token_type = get_jwt()["type"]  # Access or Refresh  

        token = TokenBlacklist(jti=jti, token_type=token_type)  

        # Log the action  
        log = ActionLog(  
            user_id=get_jwt_identity(),  
            action="logout",  
            resource="Token",  
            details=json.dumps({"jti": jti}),  
            ip_address=request.remote_addr,  
            user_agent=request.headers.get('User-Agent')  
        )  

        try:  
            db.session.add(token)  
            db.session.add(log)  
            db.session.commit()  
            return {"message": "Successfully logged out"}, 200  
        except Exception as e:  
            db.session.rollback()  # Rollback the session  
            return {"message": "Token already logged out"}, 400

@auth_ns.route('/refresh')
class RefreshToken(Resource):
    @original_jwt_required(refresh=True)
    def post(self):
        """Refresh access token"""
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)

        # Log action
        log = ActionLog(
            user_id=current_user_id,
            action="refresh_token",
            resource="Token",
            details=json.dumps({"user_id": current_user_id}),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)
        db.session.commit()

        return {"access_token": access_token}, 200

@auth_ns.route('/me')
class Me(Resource):
    @jwt_required()
    def get(self):
        """Get current user information"""
        current_user_id = get_jwt_identity()
        user = get_user_by_id(current_user_id)

        if user:
            # Log action
            log = ActionLog(
                user_id=current_user_id,
                action="view_profile",
                resource="User",
                resource_id=user.id,
                details=json.dumps({"username": user.username}),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(log)
            db.session.commit()

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "department": user.department
            }, 200

        return {"error": "User not found"}, 404

@auth_ns.route('/forgot-password')  
class ForgotPassword(Resource):  
    @auth_ns.expect(forgot_password_model)  
    def post(self):  
        """Send OTP for password reset"""  
        data = request.json  
        email = data.get('email')  

        if not email:  
            return {"error": "Email is required"}, 400  

        user = User.query.filter_by(email=email).first()  
        if not user:  
            return {"error": "User with this email not found"}, 404  

        # Generate a temporary OTP  
        otp = ''.join(random.choices(string.digits, k=6))  # Generate a 6-digit OTP  
        expiry_time = datetime.utcnow() + timedelta(minutes=30)  # Set OTP expiry to 5 minutes  

        # Store the OTP and its expiry in the database (you may need to create a new model for this)  
        user.otp = otp  
        user.otp_expiry = expiry_time  
        db.session.commit()  

        # Send email with the OTP  
        send_otp_email(email, otp)  

        # Log action  
        log = ActionLog(  
            user_id=user.id,  
            action="forgot_password",  
            resource="User",  
            resource_id=user.id,  
            details=json.dumps({"email": email}),  
            ip_address=request.remote_addr,  
            user_agent=request.headers.get('User-Agent')  
        )  
        db.session.add(log)  
        db.session.commit()  

        return {"message": "OTP sent to your email"}, 200 

@auth_ns.route('/reset-password')  
class ResetPassword(Resource):  
    @auth_ns.expect(reset_password_model)  # Ensure this model includes 'email', 'otp', and 'new_password'  
    def post(self):  
        """Reset user password using OTP code"""  
        # Extract the email, OTP, and new password from the payload  
        data = request.json  
        email = data.get('email')  
        otp = data.get('otp')  
        new_password = data.get('new_password')  

        if not email or not otp or not new_password:  
            return {"error": "Email, OTP, and new password are required"}, 400  

        try:  
            # Retrieve the user based on the provided email  
            user = User.query.filter_by(email=email).first()  

            # Check if user exists and validate OTP  
            if not user or user.otp != otp or user.otp_expiry < datetime.utcnow():  
                return {"error": "Invalid or expired OTP"}, 400  

            # Set new password (ensure you hash it appropriately)  
            user.set_password(new_password)  
            user.otp = None  # Clear OTP after use  
            user.otp_expiry = None  # Clear expiry after use  
            db.session.commit()  

            # Log the action  
            log = ActionLog(  
                user_id=user.id,  
                action="reset_password",  
                resource="User",  
                resource_id=user.id,  
                details=json.dumps({"email": email}),  # Log details for tracking  
                ip_address=request.remote_addr,  
                user_agent=request.headers.get('User-Agent')  
            )  
            db.session.add(log)  
            db.session.commit()  

            return {"message": "Password reset successfully"}, 200  

        except Exception as e:  
            return {"error": str(e)}, 400

@auth_ns.route('/update-username')
class UpdateUsername(Resource):
    @auth_ns.expect(update_username_model)
    @jwt_required()
    def patch(self):
        """Update the username of the current user"""
        data = request.json
        new_username = data.get('new_username')

        if not new_username:
            return {"error": "New username is required"}, 400

        current_user_id = get_jwt_identity()
        user = get_user_by_id(current_user_id)

        if User.query.filter_by(username=new_username).first():
            return {"error": "Username already taken"}, 400

        old_username = user.username
        user.username = new_username
        db.session.commit()

        # Log action
        log = ActionLog(
            user_id=current_user_id,
            action="update_username",
            resource="User",
            resource_id=user.id,
            details=json.dumps({"old_username": old_username, "new_username": new_username}),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)
        db.session.commit()

        return {"message": "Username updated successfully"}, 200

@auth_ns.route('/update-email')
class UpdateEmail(Resource):
    @auth_ns.expect(update_email_model)
    @jwt_required()
    def patch(self):
        """Update the email of the current user"""
        data = request.json
        new_email = data.get('new_email')

        if not new_email:
            return {"error": "New email is required"}, 400

        current_user_id = get_jwt_identity()
        user = get_user_by_id(current_user_id)

        if User.query.filter_by(email=new_email).first():
            return {"error": "Email already taken"}, 400

        old_email = user.email
        user.email = new_email
        db.session.commit()

        # Log action
        log = ActionLog(
            user_id=current_user_id,
            action="update_email",
            resource="User",
            resource_id=user.id,
            details=json.dumps({"old_email": old_email, "new_email": new_email}),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)
        db.session.commit()

        return {"message": "Email updated successfully"}, 200

@auth_ns.route('/change-password')
class ChangePassword(Resource):
    @auth_ns.expect(change_password_model)
    @jwt_required()
    def post(self):
        """Change user password"""
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not old_password or not new_password:
            return {"error": "Old password and new password are required"}, 400

        current_user_id = get_jwt_identity()
        user = get_user_by_id(current_user_id)

        if not user.check_password(old_password):
            return {"error": "Incorrect old password"}, 400

        # Update password
        user.set_password(new_password)
        db.session.commit()

        # Log action
        log = ActionLog(
            user_id=current_user_id,
            action="change_password",
            resource="User",
            resource_id=user.id,
            details=json.dumps({"action": "password changed"}),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)
        db.session.commit()

        return {"message": "Password changed successfully"}, 200

# Results routes
@results_ns.route('/submit')
class SubmitResults(Resource):
    @results_ns.expect(result_model)
    @jwt_role_required('hod', 'exam_officer', 'lecturer')
    def post(self):
        """Submit new results for a course"""
        data = request.json

        # Validate required fields in the main payload
        required_fields = ['course_code', 'course_title', 'course_unit', 'level', 
                           'faculty', 'department', 'semester_name', 'session', 'results', 'lecturers']
        error_response = check_required_fields(data, required_fields)
        if error_response:
            return error_response

        lecturer_id = get_jwt_identity()

        # Fetch or create the course
        course = get_or_create_course({
            "code": data['course_code'],
            "title": data['course_title'],
            "unit": data['course_unit'],
            "department": data['department'],
            "faculty": data['faculty'],
            "level": data['level']
        })

        # Fetch or create the semester
        semester = get_or_create_semester(data['session'], data['semester_name'])

        # Check if a result for this course and semester already exists
        result = Result.query.filter_by(
            course_id=course.id,
            semester_id=semester.id
        ).first()

        if not result:
            # Create a new result
            result = Result(
                course_id=course.id,
                semester_id=semester.id,
                uploader_lecturer_id=lecturer_id,
                upload_date=datetime.utcnow()
            )
            db.session.add(result)
            db.session.flush()  # Get `result.id` for linking scores

        try:
            # Process each score
            for result_data in data['results']:
                # Validate required fields in each result
                required_result_fields = ['registration_number', 'ca_score', 'exam_score', 'total_score', 'grade']
                error_response = check_required_fields(result_data, required_result_fields)
                if error_response:
                    return error_response

                # Fetch or create the student
                student = get_student_by_registration(result_data['registration_number'])
                if not student:
                    student = Student(
                        registration_number=result_data['registration_number'],
                        name=result_data['student_name'],
                        department=data['department']
                    )
                    db.session.add(student)
                    db.session.flush()  # Ensure `student.id` is available

                # Save the score linked to the result
                score = Score(
                    result_id=result.id,  # Link the score to the shared result
                    student_id=student.id,
                    continuous_assessment=result_data['ca_score'],
                    exam_score=result_data['exam_score'],
                    total_score=result_data['total_score'],
                    grade=result_data['grade']
                )
                db.session.add(score)

            # Commit all changes
            db.session.commit()

            # Log action for submitting results
            current_user_id = get_jwt_identity()
            log = ActionLog(
                user_id=current_user_id,
                action="submit_result",
                resource="Result",
                resource_id=result.id,
                details=json.dumps({"course_code": data['course_code'], "semester_name": data['semester_name']}),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(log)
            db.session.commit()

            return {"message": "Results submitted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

@results_ns.route('/list')
class ResultListView(Resource):
    @results_ns.doc(params={
        'department': 'Filter by department (optional)',
        'course_code': 'Filter by course code (optional)',
        'semester': 'Filter by semester (optional)',
        'session': 'Filter by academic session (optional)',
        'page': 'Page number for pagination (optional, default=1)',
        'per_page': 'Number of results per page (optional, default=10)'
    })
    @results_ns.response(200, 'Results list retrieved successfully')
    @results_ns.doc(security='Bearer')
    @jwt_role_required('hod', 'exam_officer', 'lecturer')
    def get(self):
        """Get a list of all result metadata with optional filters"""
        # Retrieve filters from query parameters
        department = request.args.get('department')
        course_code = request.args.get('course_code')
        semester = request.args.get('semester')
        session = request.args.get('session')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Initialize query
        query = Result.query

        # Apply filters
        if department:
            query = query.join(Course).filter(Course.department.ilike(f"%{department}%"))
        if course_code:
            query = query.join(Course).filter(Course.code.ilike(f"%{course_code}%"))
        if semester:
            query = query.join(Semester).filter(Semester.name.ilike(f"%{semester}%"))
        if session:
            query = query.join(Semester).filter(Semester.name.ilike(f"%{session}%"))

        # Access Control: Lecturers can only view results they've submitted or the ones associated with courses they teach
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if current_user.role == 'lecturer':
            # Check results that the lecturer has submitted or courses they are teaching
            query = query.filter(
                (Result.uploader_lecturer_id == current_user_id) |  # Submitted by lecturer
                (Course.lecturers.any(id=current_user_id))  # Course lecturer
            )

        # Fetch paginated results
        results = query.paginate(page=page, per_page=per_page, error_out=False)

        # Prepare metadata for each result
        result_list = []
        for result in results.items:
            result_list.append({
                "id": result.id,
                "course_code": result.course.code,
                "course_title": result.course.title,
                "semester": result.semester.name,
                "uploaded_by": result.uploader.username,
                "upload_date": result.upload_date.isoformat() if result.upload_date else None,
                "department": result.course.department,
                "faculty": result.course.faculty,
                "num_scores": len(result.scores)  # Count of scores associated with the result
            })

        return {
            "results": result_list,
            "total_results": results.total,
            "current_page": results.page,
            "total_pages": results.pages,
            "per_page": results.per_page
        }, 200

@results_ns.route('/<int:result_id>')
class ResultDetailView(Resource):
    @results_ns.response(200, 'Result details retrieved successfully')
    @results_ns.response(404, 'Result not found')
    @results_ns.doc(security='Bearer')
    @jwt_role_required('hod', 'exam_officer', 'lecturer')
    def get(self, result_id):
        """Get detailed information for a specific result"""
        result = Result.query.get(result_id)
        if not result:
            return {"error": "Result not found"}, 404

        # Access Control: Lecturers can only view results they've submitted or courses they teach
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if current_user.role == 'lecturer':
            if result.uploader_lecturer_id != current_user_id and current_user not in result.course.lecturers:
                return {"error": "You are not authorized to view this result"}, 403

        # Fetch the associated scores for the result, sorted by student name
        scores = sorted(result.scores, key=lambda x: x.student.name.lower())  # Sorting by student name A-Z

        # Prepare the response
        response = {
            "id": result.id,
            "course_code": result.course.code,
            "course_title": result.course.title,
            "semester": result.semester.name,
            "uploaded_by": result.uploader.username,
            "upload_date": result.upload_date.isoformat() if result.upload_date else None,  # Serialize datetime
            "department": result.course.department,
            "faculty": result.course.faculty,
            "scores": [
                {
                    "student_name": score.student.name,
                    "registration_number": score.student.registration_number,
                    "continuous_assessment": score.continuous_assessment,
                    "exam_score": score.exam_score,
                    "total_score": score.total_score,
                    "grade": score.grade
                } for score in scores
            ]
        }

        # Log the action for viewing result details
        log = ActionLog(
            user_id=current_user_id,
            action="view_result_detail",
            resource="Result",
            resource_id=result.id,
            details=json.dumps({"course_code": result.course.code, "semester_name": result.semester.name}),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)
        db.session.commit()

        return response, 200

@results_ns.route('/by-registration')
class ResultsByRegistration(Resource):
    @results_ns.doc(params={
        'registration_number': 'Student registration number (required)',
        'session': 'Academic session (optional)'
    })
    @results_ns.response(200, 'Results retrieved successfully')
    @results_ns.response(404, 'Student not found')
    @results_ns.response(400, 'Missing required parameters')
    @results_ns.doc(security='Bearer')
    @jwt_role_required('hod', 'exam_officer')
    def get(self):
        """Get results for a specific student by their registration number"""
        # Get query parameters
        registration_number = request.args.get('registration_number')
        session = request.args.get('session')

        # Validate the registration number
        if not registration_number:
            return {"error": "Missing required query parameter: registration_number"}, 400

        # Fetch the student
        student = get_student_by_registration(registration_number)
        if not student:
            return {"error": f"Student with registration number '{registration_number}' not found."}, 404

        # Query scores and join with related models
        query = Score.query.options(
            joinedload(Score.result).joinedload(Result.course),
            joinedload(Score.result).joinedload(Result.semester)
        ).filter(Score.student_id == student.id)

        if session:
            query = query.join(Result.semester).filter(Semester.name.like(f'{session}%'))

        scores = query.all()

        # Handle case where no results are found
        if not scores:
            return {"error": f"No results found for student '{registration_number}'."}, 404

        # Process scores data grouped by session and semester
        grouped_results, total_credit_earned, total_grade_point = process_scores_data(scores)

        session_results = []
        for session_name, session_data in grouped_results.items():
            session_results.append({
                "session": session_name,
                "overall_credit_earned": sum(
                    semester["total_credit_earned"] for semester in session_data["results_by_semester"].values()
                ),
                "overall_grade_point": sum(
                    semester["total_grade_point"] for semester in session_data["results_by_semester"].values()
                ),
                "results_by_semester": session_data["results_by_semester"]
            })

        # Calculate CGPA
        cgpa = round(total_grade_point / total_credit_earned, 2) if total_credit_earned > 0 else 0

        # Log the action
        current_user_id = get_jwt_identity()
        log = ActionLog(
            user_id=current_user_id,
            action="view_results_by_registration",
            resource="Score",
            resource_id=None,
            details=json.dumps({
                "registration_number": registration_number,
                "session": session,
                "results_count": len(scores),
                "cgpa": cgpa
            }),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)
        db.session.commit()

        # Prepare response data
        return {
            "student_name": student.name,
            "registration_number": student.registration_number,
            "session": session if session else "All Sessions",
            "total_credit_earned": total_credit_earned,
            "total_grade_point": total_grade_point,
            "cgpa": cgpa,
            "results": session_results
        }, 200

@results_ns.route('/<int:result_id>/update-score')
class UpdateOrCreateScore(Resource):
    @results_ns.expect(score_update_model)
    @results_ns.response(200, 'Score updated or created successfully')
    @results_ns.response(404, 'Result or student not found')
    @results_ns.response(400, 'Invalid request payload')
    @jwt_role_required('hod', 'exam_officer', 'lecturer')
    def patch(self, result_id):
        """Update or create a score for a result, including adding a new student"""
        data = request.json

        # Validate required parameters
        registration_number = data.get("registration_number")
        if not registration_number:
            return {"error": "Registration number is required"}, 400

        # Validate if the result exists
        result = Result.query.get(result_id)
        if not result:
            return {"error": f"Result with ID {result_id} not found"}, 404

        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        # Ensure the lecturer is either the uploader or affiliated with the course
        if result.uploader_lecturer_id != current_user_id or current_user not in result.course.lecturers:
            return {"error": "You are not authorized to update this result."}, 403

        # Fetch or create the student
        student = Student.query.filter_by(registration_number=registration_number).first()
        if not student:
            # If the student doesn't exist, create a new student
            if not data.get("student_name"):
                return {"error": "Student name is required for new students"}, 400
            student = Student(
                registration_number=registration_number,
                name=data["student_name"],
                department=result.course.department  # Use the department linked to the course
            )
            db.session.add(student)
            db.session.flush()  # Get the `student.id` before proceeding

        # Fetch or create the score
        score = Score.query.filter_by(result_id=result.id, student_id=student.id).first()
        if not score:
            # Create a new score if it doesn't exist
            score = Score(
                result_id=result.id,
                student_id=student.id
            )
            db.session.add(score)

        try:
            # Update fields if provided in the payload
            if "ca_score" in data:
                score.continuous_assessment = data["ca_score"]
            if "exam_score" in data:
                score.exam_score = data["exam_score"]
            if "total_score" in data:
                score.total_score = data["total_score"]
            else:
                # Calculate total_score automatically if ca_score or exam_score is updated
                score.total_score = score.continuous_assessment + score.exam_score

            if "grade" in data:
                score.grade = data["grade"]

            # Commit changes
            db.session.commit()

            # Log the action
            log = ActionLog(
                user_id=current_user_id,
                action="update_or_create_score",
                resource="Score",
                resource_id=score.id,
                details=json.dumps(data),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(log)
            db.session.commit()

            return {"message": "Score updated or created successfully"}, 200

        except Exception as e:
            db.session.rollback()
            return {"error": f"An error occurred: {str(e)}"}, 500

@results_ns.route('/<int:result_id>/update-meta')
class UpdateResultMeta(Resource):
    @results_ns.expect(result_update_model)
    @results_ns.response(200, 'Result metadata updated successfully')
    @results_ns.response(404, 'Result not found')
    @results_ns.response(400, 'Invalid request payload')
    @jwt_role_required('hod', 'exam_officer', 'lecturer')
    def patch(self, result_id):
        """Update metadata for a specific result"""
        data = request.json

        # Fetch the result by ID
        result = Result.query.get(result_id)
        if not result:
            return {"error": f"Result with ID {result_id} not found."}, 404

        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        # Ensure the lecturer is either the uploader or affiliated with the course
        if result.uploader_lecturer_id != current_user_id or current_user not in result.course.lecturers:
            return {"error": "You are not authorized to update this result metadata."}, 403

        # Dynamically set the uploader_lecturer_id from the current user (using JWT)
        uploader_lecturer_id = get_jwt_identity()

        # Update fields dynamically if present in the payload
        try:
            # Check and update course code if provided
            if "course_code" in data:
                course = Course.query.filter_by(code=data["course_code"]).first()
                if not course:
                    return {"error": f"Course with code '{data['course_code']}' not found."}, 404
                result.course_id = course.id

            # Check and update semester and session if provided
            if "semester_name" in data and "session" in data:
                semester_name = f"{data['session']} {data['semester_name']}"
                semester = Semester.query.filter_by(name=semester_name).first()
                if not semester:
                    return {"error": f"Semester '{semester_name}' not found."}, 404
                result.semester_id = semester.id

            # Update course title and unit if provided
            if "course_title" in data:
                result.course.title = data["course_title"]
            if "course_unit" in data:
                result.course.unit = data["course_unit"]

            # Update department if provided
            if "department" in data:
                result.course.department = data["department"]

            # If uploader_lecturer_id is provided, update it
            result.uploader_lecturer_id = uploader_lecturer_id

            # Optionally update the original file if provided
            if "original_file" in data:
                result.original_file = data["original_file"]

            # Commit the updates
            db.session.commit()

            # Log the action
            log = ActionLog(
                user_id=uploader_lecturer_id,
                action="update_result_meta",
                resource="Result",
                resource_id=result_id,
                details=json.dumps(data),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(log)
            db.session.commit()

            return {"message": "Result metadata updated successfully"}, 200

        except Exception as e:
            db.session.rollback()
            return {"error": f"An error occurred: {str(e)}"}, 500

@results_ns.route('/search')
class SearchResults(Resource):
    @results_ns.doc(params={
        'course_code': 'Course code to filter results',
        'department': 'Department to filter results',
        'faculty': 'Faculty to filter results',
        'semester_name': 'Semester name to filter results',
        'session': 'Session to filter results',
        'registration_number': 'Student registration number to filter results',
        'page': 'Page number for pagination',
        'per_page': 'Number of results per page'
    })
    @results_ns.response(200, 'Search results retrieved successfully')
    @results_ns.response(400, 'Invalid request parameters')
    @results_ns.doc(security='Bearer')
    @jwt_role_required('hod', 'exam_officer', 'lecturer')
    def get(self):
        """Search results based on multiple criteria"""
        # Query parameters
        course_code = request.args.get('course_code')
        department = request.args.get('department')
        faculty = request.args.get('faculty')
        semester_name = request.args.get('semester_name')
        session = request.args.get('session')
        registration_number = request.args.get('registration_number')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Initialize query
        query = Result.query.join(Course).join(Semester).join(Score)

        # Apply filters
        if course_code:
            query = query.filter(Course.code.ilike(f"%{course_code}%"))
        if department:
            query = query.filter(Course.department.ilike(f"%{department}%"))
        if faculty:
            query = query.filter(Course.faculty.ilike(f"%{faculty}%"))
        if semester_name:
            query = query.filter(Semester.name.ilike(f"%{semester_name}%"))
        if session:
            query = query.filter(Semester.name.like(f"{session} %"))
        if registration_number:
            query = query.join(Score).filter(Score.student_id == Student.query.filter_by(
                registration_number=registration_number).with_entities(Student.id))

        # Paginate results
        results = query.paginate(page=page, per_page=per_page, error_out=False)

        # Prepare response data
        search_results = []
        for result in results.items:
            search_results.append({
                "id": result.id,
                "course_code": result.course.code,
                "course_title": result.course.title,
                "semester": result.semester.name,
                "department": result.course.department,
                "faculty": result.course.faculty,
                "upload_date": result.upload_date.isoformat() if result.upload_date else None,
                "num_scores": len(result.scores)
            })

        # Return paginated results
        return {
            "search_results": search_results,
            "total_results": results.total,
            "current_page": results.page,
            "total_pages": results.pages,
            "per_page": results.per_page
        }, 200

@results_ns.route('/delete/<int:result_id>')
class DeleteResult(Resource):
    @results_ns.response(200, 'Result deleted successfully')
    @results_ns.response(404, 'Result not found')
    @results_ns.doc(security='Bearer')
    @jwt_role_required('hod', 'exam_officer', 'lecturer')
    def delete(self, result_id):
        """Delete a result and its associated scores"""
        # Fetch the result and pre-load relationships
        result = Result.query.options(
            joinedload(Result.course),
            joinedload(Result.semester)
        ).filter_by(id=result_id).first()

        if not result:
            return {"error": "Result not found"}, 404

        try:
            # Fetch all associated scores
            scores = Score.query.filter_by(result_id=result.id).all()

            # Store relevant details for logging
            course_code = result.course.code if result.course else None
            course_title = result.course.title if result.course else None
            semester_name = result.semester.name if result.semester else None

            # Delete all associated scores
            for score in scores:
                db.session.delete(score)

            # Delete the result
            db.session.delete(result)
            db.session.commit()

            # Log the action
            current_user_id = get_jwt_identity()
            log = ActionLog(
                user_id=current_user_id,
                action="delete_result",
                resource="Result",
                resource_id=result_id,
                details=json.dumps({
                    "course_code": course_code,
                    "course_title": course_title,
                    "semester": semester_name,
                    "deleted_scores_count": len(scores)
                }),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(log)
            db.session.commit()

            return {
                "message": "Result and its associated scores deleted successfully",
                "deleted_scores_count": len(scores)
            }, 200

        except Exception as e:
            # Rollback in case of any error
            db.session.rollback()
            return {"error": f"An error occurred while deleting the result: {str(e)}"}, 500

# File Upload Route
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type='FileStorage', required=True)

@results_ns.route('/upload')
class UploadResults(Resource):
    upload_parser = api.parser()
    upload_parser.add_argument('file', location='files', type='FileStorage', required=True)

    @results_ns.expect(upload_parser)
    @results_ns.doc(security='Bearer')
    @jwt_role_required('hod', 'exam_officer', 'lecturer')
    def post(self):
        """Upload and process a results file"""
        if 'file' not in request.files:
            return {"error": "No file part"}, 400

        file = request.files['file']
        filepath, error = save_file(file)
        if error:
            return {"error": error}, 400

        try:
            # Process the file
            extraction_result, message = process_uploaded_file(filepath)
            if extraction_result is None:
                return {"error": message}, 400

            header_info, results_data = extraction_result
            uploader_id = get_jwt_identity()

            # Fetch or create the course
            course = Course.query.filter_by(code=header_info['course_code']).first()

            if not course:
                # If course doesn't exist, create it
                course = Course(
                    code=header_info['course_code'],
                    title=header_info['course_title'],
                    unit=header_info['course_unit'],
                    department=header_info['department'],
                    faculty=header_info['faculty'],
                    level='100'  # You can adjust this based on your payload data
                )
                db.session.add(course)
                db.session.flush()  # Ensure the course ID is available

            current_user = User.query.get(uploader_id)
            if current_user.role == 'lecturer' and current_user not in course.lecturers:
                return {"error": "You are not authorized to upload results for this course."}, 403

            # Save extracted data to the database
            file_info = {
                'filename': file.filename,
                'uploader_id': uploader_id
            }

            success, db_message = save_results_to_db(header_info, results_data, file_info)
            if not success:
                return {"error": db_message}, 500

            return {
                "message": "File processed and results saved successfully",
                "records": len(results_data)
            }, 200

        except Exception as e:
            return {"error": str(e)}, 500



from sqlalchemy.orm import joinedload

@security_ns.route('/action-logs')
class ActionLogView(Resource):
    @results_ns.doc(params={
        'page': 'Page number for pagination (optional, default=1)',
        'per_page': 'Number of results per page (optional, default=10)'
    })
    @security_ns.response(200, 'Action logs retrieved successfully')
    @security_ns.response(403, 'Forbidden')
    @security_ns.doc(security='Bearer')
    @jwt_role_required('hod', 'admin')  # Only HODs and Admins can access this
    def get(self):
        """Get all action logs."""
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        try:
            # Fetch paginated action logs and ensure the 'user' relationship is eagerly loaded
            action_logs = ActionLog.query.options(joinedload(ActionLog.user)).order_by(ActionLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)

            # Prepare the response data
            logs_data = []
            for log in action_logs.items:
                logs_data.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.user.username if log.user else None,  # Safely access the 'username'
                    "action": log.action,
                    "resource": log.resource,
                    "resource_id": log.resource_id,
                    "details": log.details,
                    "timestamp": log.timestamp.isoformat(),
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent
                })

            # Return the action logs with pagination info
            return {
                "action_logs": logs_data,
                "total_results": action_logs.total,
                "current_page": action_logs.page,
                "total_pages": action_logs.pages,
                "per_page": action_logs.per_page
            }, 200

        except Exception as e:
            return {"error": str(e)}, 500


# Protected Route Example
@auth_ns.route('/protected')
class Protected(Resource):
    @auth_ns.response(200, 'Token is valid')
    @auth_ns.doc(security='Bearer')
    @jwt_required()
    def get(self):
        """Test protected route"""
        current_user_id = get_jwt_identity()
        user = get_user_by_id(current_user_id)
        return {
            "logged_in_as": user.username,
            "role": user.role
        }, 200

# Health Check Route
@api.route('/health')
class Health(Resource):
    @api.response(200, 'Server is healthy')
    def get(self):
        """Test health check route"""
        return {"message": "Server is healthy"}, 200


# Configure JWT for Swagger
authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token"
    },
}

api.authorizations = authorizations

# Initialize the app with the blueprint
def init_app(app):
    app.register_blueprint(api_blueprint)