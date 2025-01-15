# flask-app/app/utils.py
import pypdf
from docx import Document
from openpyxl import load_workbook
import csv
from flask import jsonify, current_app
from .models import User, Course, Semester, Student, Result
from . import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from .extraction import *

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
    return jsonify({"error": message}), status_code

def get_user_by_id(user_id):
    return User.query.get(user_id)

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

def get_student_by_registration(registration_number):
    return Student.query.filter_by(registration_number=registration_number).first()

def check_required_fields(data, required_fields):
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return create_error_response(f"Missing required fields: {', '.join(missing_fields)}")
    return None

def get_or_create_course(data):
    course = Course.query.filter_by(code=data['course_code']).first()
    if not course:
        course = Course(
            code=data['course_code'],
            title=data['course_title'],
            unit=data['course_unit'],
            department=data['exam_department'],
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
    try:
        if filepath.endswith('.xlsx'):
            return extract_xlsx_data(filepath), "XLSX file processed"
        elif filepath.endswith('.docx'):
            return extract_docx_data(filepath), "DOCX file processed"
        elif filepath.endswith('.pdf'):
            return extract_pdf_data(filepath), "PDF file processed"
        elif filepath.endswith('.csv'):
            return extract_csv_data(filepath), "CSV file processed"
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
               level='100'
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

           # Create or update result
           existing_result = Result.query.filter_by(
               student_id=student.id,
               course_id=course.id,
               semester_id=semester.id
           ).first()

           if existing_result:
               existing_result.continuous_assessment = result['continuous_assessment']
               existing_result.exam_score = result['exam_score']
               existing_result.total_score = result['total_score']
               existing_result.grade = result['grade']
           else:
               new_result = Result(
                   student_id=student.id,
                   course_id=course.id,
                   semester_id=semester.id,
                   continuous_assessment=result['continuous_assessment'],
                   exam_score=result['exam_score'],
                   total_score=result['total_score'],
                   grade=result['grade'],
                   original_file=file_info['filename'],
                   upload_date=datetime.utcnow(),
                   uploader_lecturer_id=file_info['uploader_id']
               )
               db.session.add(new_result)

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

def process_results_data(results):
    """
    Processes student results to calculate GPA and group data by session and semester.

    Args:
        results (list): A list of result objects, where each object contains course details,
                        grades, and associated semester information.

    Returns:
        tuple: A tuple containing:
            - grouped_results (dict): Results grouped by session and semester with GPA and course details.
            - overall_total_credit_earned (int): Total credits earned across all sessions and semesters.
            - overall_total_grade_point (float): Total grade points across all sessions and semesters.
    """
    grouped_results = {}
    overall_total_credit_earned = 0
    overall_total_grade_point = 0

    for result in results:
        try:
            # Extract session and semester names
            session_name, semester_name = result.semester.name.split(" ")

            # Initialize session data if not present
            if session_name not in grouped_results:
                grouped_results[session_name] = {
                    "results_by_semester": {},
                    "overall_total_credit_earned": 0,
                    "overall_total_grade_point": 0
                }

            # Initialize semester data if not present
            if semester_name not in grouped_results[session_name]["results_by_semester"]:
                grouped_results[session_name]["results_by_semester"][semester_name] = {
                    "total_credit_earned": 0,
                    "total_grade_point": 0,
                    "courses": [],
                    "GPA": 0
                }

            # Calculate points for the course
            point = calc_point(result.grade, result.course.unit)

            # Update semester totals
            semester_data = grouped_results[session_name]["results_by_semester"][semester_name]
            semester_data["total_credit_earned"] += result.course.unit
            semester_data["total_grade_point"] += point

            # Update overall totals
            overall_total_credit_earned += result.course.unit
            overall_total_grade_point += point

            # Append course details
            semester_data["courses"].append({
                "course_code": result.course.code,
                "course_title": result.course.title,
                "course_unit": result.course.unit,
                "level": result.course.level,
                "semester": semester_name,
                "continuous_assessment": result.continuous_assessment,
                "exam_score": result.exam_score,
                "total_score": result.total_score,
                "grade": result.grade,
                "point": point
            })

        except AttributeError as e:
            print(f"Error processing result: {e}")
            continue  # Skip malformed result

    # Calculate GPA for each semester
    for session_data in grouped_results.values():
        for semester_name, semester_data in session_data["results_by_semester"].items():
            total_credit = semester_data["total_credit_earned"]
            total_points = semester_data["total_grade_point"]
            semester_data["GPA"] = total_points / total_credit if total_credit > 0 else 0

    return grouped_results, overall_total_credit_earned, overall_total_grade_point
