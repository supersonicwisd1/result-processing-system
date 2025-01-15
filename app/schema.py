# flask-app/app/schema.py
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import Student, Course, Result

class StudentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Student
        load_instance = True

class CourseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Course
        load_instance = True

class ResultSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Result
        load_instance = True
