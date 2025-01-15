# flask-app/app/routes.py
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .utils import (create_error_response, get_user_by_id, get_user_by_username,
                    get_student_by_registration, check_required_fields,
                    get_or_create_course, get_or_create_semester, process_result, save_file, save_results_to_db,
                    process_uploaded_file, process_results_data)
from .models import User, db, Result, Student, Course, Semester
from .constants import ALLOWED_ROLES, UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from functools import wraps
from flask_restx import Api, Resource, fields, Namespace

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

# Add namespaces to API
api.add_namespace(auth_ns)
api.add_namespace(results_ns)
api.add_namespace(course_ns)
api.add_namespace(student_ns)

# Models for Swagger documentation
user_model = api.model('User', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password'),
    'role': fields.String(required=True, description='User role', enum=ALLOWED_ROLES)
})

login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

student_result_model = api.model('StudentResult', {
    'registration_number': fields.String(required=True, description='Student registration number'),
    'ca_score': fields.Float(required=True, description='Continuous Assessment score'),
    'exam_score': fields.Float(required=True, description='Examination score'),
    'total_score': fields.Float(required=True, description='Total score'),
    'grade': fields.String(required=True, description='Grade achieved')
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

# Authorization decorator
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            current_user = get_user_by_id(current_user_id)
            if current_user.role not in roles:
                return {"error": "You are not authorized to access this resource"}, 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# JWT role decorator
def jwt_role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
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
        password = data.get('password')
        role = data.get('role')

        if not username or not password or not role:
            return create_error_response("Username, password, and role are required")
        if role not in ALLOWED_ROLES:
            return create_error_response(f"Invalid role. Allowed roles are {', '.join(ALLOWED_ROLES)}")

        existing_user = get_user_by_username(username)
        if existing_user:
            return create_error_response("User with this username already exists")

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return {"message": "User registered successfully"}, 201

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Login successful')
    @auth_ns.response(401, 'Invalid credentials')
    def post(self):
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {"error": "Username and password required"}, 400

        user = get_user_by_username(username)
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.id)
            return {"access_token": access_token, "role": user.role}
        
        return {"error": "Invalid credentials"}, 401

# Results routes
@results_ns.route('/submit')
class SubmitResults(Resource):
    @results_ns.expect(result_model)
    @results_ns.response(200, 'Results submitted successfully')
    @results_ns.response(400, 'Validation error')
    @results_ns.response(401, 'Unauthorized')
    @results_ns.doc(security='Bearer')
    @jwt_required()
    def post(self):
        """Submit new results for a course"""
        data = request.json
        required_fields = ['course_code', 'course_title', 'course_unit', 'level', 
                          'faculty', 'exam_department', 'semester_name', 'session', 'results']
        
        error_response = check_required_fields(data, required_fields)
        if error_response:
            return error_response
        
        lecturer_id = get_jwt_identity()
        course = get_or_create_course(data)

        if data.get('lecturers'):
            lecturers = User.query.filter(User.id.in_(data['lecturers'])).all()
            if lecturers:
                course.lecturers = lecturers

        semester = get_or_create_semester(data['session'], data['semester_name'])

        for result_data in data['results']:
            error = process_result(result_data, course, semester, lecturer_id)
            if error:
                return error
        
        db.session.commit()
        return {"message": "Results submitted successfully"}, 200

@results_ns.route('/by-course')
class ResultsByCourse(Resource):
    @results_ns.doc(params={
        'course_code': 'Course code',
        'semester_name': 'Semester name',
        'session': 'Academic session'
    })
    # @results_ns.expect(api.model('DepartmentRequest', {
    #     'course_code': fields.String(required=True),
    #     'semester_name': fields.String(required=False),
    #     'session': fields.String(required=False)
    # }))
    @results_ns.response(200, 'Results retrieved successfully')
    @results_ns.response(404, 'Course not found')
    @results_ns.doc(security='Bearer')
    @jwt_required()
    def get(self):
        """Get results for a specific course"""
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        course_code = request.args.get('course_code')
        semester_name = request.args.get('semester_name')
        session = request.args.get('session')

        if not course_code or not session or not semester_name:
            return {"error": "Missing required course or session details"}, 400

        course = Course.query.filter_by(code=course_code).first()
        if not course:
            return {"error": "Course not found"}, 404

        if current_user.role == 'lecturer' and current_user not in course.lecturers:
            return {"error": "You are not authorized to access results for this course"}, 403

        semester = Semester.query.filter_by(name=f"{session} {semester_name}").first()
        if not semester:
            return {"error": "Semester not found"}, 404

        results = Result.query.filter_by(course_id=course.id, semester_id=semester.id).all()
        if not results:
            return {"error": f"No results found for course {course_code}"}, 404

        results_data = []
        for result in results:
            results_data.append({
                "student_name": result.student.name,
                "registration_number": result.student.registration_number,
                "student_department": result.student.department,
                "ca_score": result.continuous_assessment,
                "exam_score": result.exam_score,
                "total_score": result.total_score,
                "grade": result.grade
            })

        return {
            "course_code": course.code,
            "course_title": course.title,
            "course_department": course.department,
            "course_unit": course.unit,
            "faculty": course.faculty,
            "semester": semester_name,
            "session": session,
            "results": results_data
        }, 200

@results_ns.route('/by-registration')
class ResultsByRegistration(Resource):
    @results_ns.doc(params={
        'registration_number': 'Student registration number',
        'session': 'Academic session (optional)'
    })
    @results_ns.response(200, 'Results retrieved successfully')
    @results_ns.response(404, 'Student not found')
    @results_ns.doc(security='Bearer')
    @jwt_role_required('hod', 'exam_officer')
    def get(self):
        """Get results for a specific student"""
        registration_number = request.args.get('registration_number')
        session = request.args.get('session')

        if not registration_number:
            return {"error": "Missing required query parameter: registration_number"}, 400

        student = get_student_by_registration(registration_number)
        if not student:
            return {"error": "Student not found"}, 404

        if session:
            results = Result.query.join(Semester).filter(
                Result.student_id == student.id,
                Semester.name.like(f'{session}%')
            ).all()
        else:
            results = Result.query.filter_by(student_id=student.id).join(Semester).all()

        if not results:
            return {"error": f"No results found for student {registration_number}"}, 404

        grouped_results, total_credit_earned, total_grade_point = process_results_data(results)

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

        cgpa = round(total_grade_point / total_credit_earned, 2) if total_credit_earned > 0 else 0

        return {
            "student_name": student.name,
            "registration_number": student.registration_number,
            "session": session if session else "All Sessions",
            "total_credit_earned": total_credit_earned,
            "total_grade_point": total_grade_point,
            "cgpa": cgpa,
            "results": session_results
        }, 200

@results_ns.route('/update')
class UpdateResult(Resource):
    @results_ns.doc(params={
        'course_code': 'Course code',
        'registration_number': 'Student registration number',
        'session': 'Academic session',
        'semester': 'Semester name'
    })
    @results_ns.response(200, 'Result updated successfully')
    @results_ns.response(404, 'Result not found')
    @results_ns.doc(security='Bearer')
    @jwt_required()
    def put(self):
        """Update an existing result"""
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if current_user.role not in ['hod', 'exam_officer', 'lecturer']:
            return {"error": "You are not authorized to update results"}, 403

        data = request.json
        course_code = data.get('course_code')
        registration_number = data.get('registration_number')
        session = data.get('session')
        semester_name = data.get('semester')

        if not all([course_code, registration_number, session, semester_name]):
            return {"error": "Missing required fields"}, 400

        course = Course.query.filter_by(code=course_code).first()
        if not course:
            return {"error": "Course not found"}, 404

        student = get_student_by_registration(registration_number)
        if not student:
            return {"error": "Student not found"}, 404

        semester = Semester.query.filter_by(name=f"{session} {semester_name}").first()
        if not semester:
            return {"error": "Semester not found"}, 404

        result = Result.query.filter_by(
            student_id=student.id,
            course_id=course.id,
            semester_id=semester.id
        ).first()

        if not result:
            return {"error": "Result not found"}, 404

        if current_user.role == 'lecturer' and result.lecturer_id != current_user.id:
            return {"error": "You are not authorized to update this result"}, 403

        for field in ['ca_score', 'exam_score', 'total_score', 'grade']:
            if data.get(field) is not None:
                setattr(result, field, data[field])

        db.session.commit()
        return {"message": "Result updated successfully"}, 200

@results_ns.route('/delete/<int:result_id>')
class DeleteResult(Resource):
    @results_ns.response(200, 'Result deleted successfully')
    @results_ns.response(404, 'Result not found')
    @results_ns.doc(security='Bearer')
    @jwt_required()
    def delete(self, result_id):
        """Delete a result"""
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        result = Result.query.get(result_id)
        if not result:
            return {"error": "Result not found"}, 404
        
        if current_user.role in ['hod', 'exam_officer'] or (
            current_user.role == 'lecturer' and result.lecturer_id == current_user.id
        ):
            db.session.delete(result)
            db.session.commit()
            return {"message": "Result deleted successfully"}, 200
        else:
            return {"error": "You are not authorized to delete this result"}, 403

@results_ns.route('/by-department')
class ResultsByDepartment(Resource):
    # @results_ns.doc(params={
    #     'department': 'Department name',
    #     'session': 'Academic session',
    #     'semester': 'Semester name (optional)'
    # },
    #     security='Bearer'
    # )
    @results_ns.expect(api.model('DepartmentRequest', {
        'department': fields.String(required=True),
        'session': fields.String(required=False),
        'semester': fields.String(required=False)
    }))
    @results_ns.response(200, 'Results retrieved successfully')
    @results_ns.response(404, 'Department not found')
    @results_ns.doc(security='Bearer')
    @jwt_role_required('hod', 'exam_officer')
    def post(self):
        """Get results for a specific department"""
        data = request.json
        session = data.get('session')
        semester_name = data.get('semester')
        department = data.get('department').upper()

        if not session or not department:
            return {"error": "Missing required details"}, 400

        course = Course.query.filter_by(department=department).first()
        if not course:
            return {"error": "No courses found for department"}, 404

        semester_full_name = f"{session} {semester_name}" if semester_name else None

        if semester_name:
            semester = Semester.query.filter_by(name=semester_full_name).first()
            if not semester:
                return {"error": "Semester not found"}, 404

            results = Result.query.join(Course).join(Semester).filter(
                Semester.name.like(f"{session} {semester_name}"),
                Course.department == department     
            ).all()
        else:
            results = Result.query.join(Course).filter(
                Course.department == department
            ).all()

        if not results:
            return {"error": f"No results found for {department}"}, 404

        results_data = []
        for result in results:
            results_data.append({
                "student_name": result.student.name,
                "registration_number": result.student.registration_number,
                "courses": {
                    "code": result.course.code,
                    "title": result.course.title,
                    "unit": result.course.unit,
                    "department": result.course.department,
                    "faculty": result.course.faculty,
                    "results": {
                        "ca_score": result.continuous_assessment,
                        "exam_score": result.exam_score,
                        "total_score": result.total_score,
                        "grade": result.grade
                    }
                }
            })

        return {
            "department": department,
            "semester": semester_full_name if semester_name else "All Semesters",
            "session": session,
            "results": results_data
        }, 200

# File Upload Route
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type='FileStorage', required=True)

@results_ns.route('/upload')
class UploadResults(Resource):
    upload_parser = api.parser()
    upload_parser.add_argument('file', location='files', type='FileStorage', required=True)

    @results_ns.expect(upload_parser)
    @results_ns.doc(security='Bearer')
    @jwt_required()
    def post(self):
        if 'file' not in request.files:
            return {"error": "No file part"}, 400

        file = request.files['file']
        filepath, error = save_file(file)
        if error:
            return {"error": error}, 400

        try:
            extraction_result, message = process_uploaded_file(filepath)
            if extraction_result is None:
                return {"error": message}, 400

            header_info, results_data = extraction_result
            
            file_info = {
                'filename': file.filename,
                'uploader_id': get_jwt_identity()
            }

            success, db_message = save_results_to_db(header_info, results_data, file_info)
            if not success:
                return {"error": db_message}, 500

            return {
                "message": "File processed successfully",
                "records": len(results_data)
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