# flask-app/app/utils.py
import pypdf
from docx import Document
from openpyxl import load_workbook
import csv
from flask import jsonify, current_app
from .models import User, Course, Semester, Student, Result, Score
from . import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from .extraction import *
from app import mail
from flask_mail import Message
from flask import render_template

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xls', 'xlsx', 'docx', 'pdf'}

def calc_point(grade, course_unit):
    grade_points = {
        'A': 5,
        'B': 4,
        'C': 3,
        'D': 2,
        'E': 1,
        'F': 0
    }
    return grade_points.get(grade, 0) * course_unit

def create_error_response(message, status_code=400):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


def get_user_by_id(user_id):
    return User.query.get(user_id)

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def get_student_by_registration(registration_number):
    return Student.query.filter_by(registration_number=registration_number).first()

def check_required_fields(data, required_fields):
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return create_error_response(f"Missing required fields: {', '.join(missing_fields)}")
    return None

def get_or_create_course(data):
    course = Course.query.filter_by(code=data['code']).first()
    if not course:
        course = Course(
            code=data['code'],
            title=data['title'],
            unit=data['unit'],
            department=data['department'],
            faculty=data['faculty'],
            level=data['level']
        )
        db.session.add(course)
        db.session.flush()
    return course

def get_or_create_semester(session, semester_name):
    semester_full_name = f"{session} {semester_name}"
    semester = Semester.query.filter_by(name=semester_full_name).first()
    if not semester:
        semester = Semester(name=semester_full_name)
        db.session.add(semester)
    return semester

def process_result(result_data, course, semester, lecturer_id):
    required_fields = ['registration_number', 'student_name', 'student_department', 'ca_score', 'exam_score', 'total_score', 'grade']
    error_response = check_required_fields(result_data, required_fields)
    if error_response:
        return error_response

    student = get_student_by_registration(result_data['registration_number'])
    if not student:
        student = Student(
            name=result_data['student_name'],
            registration_number=result_data['registration_number'],
            department=result_data['student_department']
        )
        db.session.add(student)
        db.session.flush()

    result = Result.query.filter_by(
        student_id=student.id, 
        course_id=course.id, 
        semester_id=semester.id
    ).first()

    if result:
        result.continuous_assessment = result_data['ca_score']
        result.exam_score = result_data['exam_score']
        result.total_score = result_data['total_score']
        result.grade = result_data['grade']
    else:
        result = Result(
            student_id=student.id,
            course_id=course.id,
            semester_id=semester.id,
            continuous_assessment=result_data['ca_score'],
            exam_score=result_data['exam_score'],
            total_score=result_data['total_score'],
            grade=result_data['grade'],
            upload_date=datetime.now(),
            uploader_lecturer_id=lecturer_id
        )
        db.session.add(result)

    return None

def process_uploaded_file(filepath):
    """Process an uploaded file to extract results."""
    try:
        ext = os.path.splitext(filepath)[-1].lower()
        if ext == ".docx":
            return extract_docx_data(filepath), "DOCX file processed"
        elif ext == ".pdf":
            return extract_pdf_data(filepath), "PDF file processed"
        elif ext == ".csv":
            return extract_csv_data(filepath), "CSV file processed"
        elif ext == ".xlsx":
            return extract_xlsx_data(filepath), "XLSX file processed"
        else:
            return None, "Unsupported file format"  
    except Exception as e:
        return None, str(e)

def save_results_to_db(header_info, results_data, file_info):
    try:
        # Get or create course
        course = Course.query.filter_by(code=header_info['course_code']).first()
        if not course:
            course = Course(
                code=header_info['course_code'],
                title=header_info['course_title'],
                unit=header_info['course_unit'],
                department=header_info['department'],
                faculty=header_info['faculty'],
                level='100'  # You can adjust this based on your payload data
            )
            db.session.add(course)
            db.session.flush()

        # Get or create semester
        semester_name = f"{header_info['session']} {header_info['semester']}"
        semester = Semester.query.filter_by(name=semester_name).first()
        if not semester:
            semester = Semester(name=semester_name)
            db.session.add(semester)
            db.session.flush()

        # Process each result
        for result in results_data:
            # Get or create student
            student = Student.query.filter_by(
                registration_number=result['registration_number']
            ).first()

            if not student:
                student = Student(
                    registration_number=result['registration_number'],
                    name=result['name'],
                    department=result['department']
                )
                db.session.add(student)
                db.session.flush()

            # Create or update result metadata
            result_metadata = Result.query.filter_by(
                course_id=course.id,
                semester_id=semester.id,
            ).first()

            if not result_metadata:
                result_metadata = Result(
                    course_id=course.id,
                    semester_id=semester.id,
                    original_file=file_info['filename'],
                    upload_date=datetime.utcnow(),
                    uploader_lecturer_id=file_info['uploader_id']
                )
                db.session.add(result_metadata)
                db.session.flush()

            # Create or update score
            score = Score.query.filter_by(result_id=result_metadata.id, student_id=student.id).first()
            if score:
                score.continuous_assessment = result['continuous_assessment']
                score.exam_score = result['exam_score']
                score.total_score = result['total_score']
                score.grade = result['grade']
            else:
                score = Score(
                    result_id=result_metadata.id,
                    student_id=student.id,
                    continuous_assessment=result['continuous_assessment'],
                    exam_score=result['exam_score'],
                    total_score=result['total_score'],
                    grade=result['grade']
                )
                db.session.add(score)

        db.session.commit()
        return True, "Results saved successfully"

    except Exception as e:
        db.session.rollback()
        return False, str(e)

def save_file(file):
    """saving the file to the upload folder. This may be removed later since we are apporaching this based on database not file system"""
    if not file or not allowed_file(file.filename):
        return None, "Invalid file format"
    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filepath, None

def process_scores_data(scores):
    grouped_scores = {}
    overall_total_credit_earned = 0
    overall_total_grade_point = 0

    for score in scores:
        # Ensure related objects are available
        if not score.result or not score.result.course or not score.result.semester:
            continue

        result = score.result
        course = result.course
        semester = result.semester

        # Extract session and semester names
        session_name, semester_name = semester.name.split(" ")

        # Initialize session data if not present
        if session_name not in grouped_scores:
            grouped_scores[session_name] = {
                "results_by_semester": {}
            }

        # Initialize semester data if not present
        if semester_name not in grouped_scores[session_name]["results_by_semester"]:
            grouped_scores[session_name]["results_by_semester"][semester_name] = {
                "total_credit_earned": 0,
                "total_grade_point": 0,
                "courses": [],
                "GPA": 0
            }

        # Calculate grade points for the course
        point = calc_point(score.grade, course.unit)

        # Update semester totals
        semester_data = grouped_scores[session_name]["results_by_semester"][semester_name]
        semester_data["total_credit_earned"] += course.unit
        semester_data["total_grade_point"] += point
        semester_data["courses"].append({
            "course_code": course.code,
            "course_title": course.title,
            "course_unit": course.unit,
            "ca_score": score.continuous_assessment,
            "exam_score": score.exam_score,
            "total_score": score.total_score,
            "grade": score.grade,
            "point": point
        })

        # Update overall totals
        overall_total_credit_earned += course.unit
        overall_total_grade_point += point

    # Calculate GPA for each semester
    for session_data in grouped_scores.values():
        for semester_name, semester_data in session_data["results_by_semester"].items():
            total_credit = semester_data["total_credit_earned"]
            total_points = semester_data["total_grade_point"]
            semester_data["GPA"] = total_points / total_credit if total_credit > 0 else 0

    return grouped_scores, overall_total_credit_earned, overall_total_grade_point

def send_reset_email(to_email, reset_token):
    try:
        reset_url = f"http://localhost:5000/api/v1/auth/reset-password?token={reset_token}"
        msg = Message('Password Reset Request', recipients=[to_email])
        msg.body = f'Use this reset token to reset your password: {reset_token}'
        # msg.html = f'<p>Click the link below to reset your password:</p><p><a href="{reset_url}">Reset Password</a></p>'
        msg.sender = "supersonicwisdom@gmail.com"
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
