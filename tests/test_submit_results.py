import unittest
from flask_jwt_extended import create_access_token
from app import create_app, db
from app.models import User, Course, Student, Result, Semester

class SubmitResultsTestCase(unittest.TestCase):

    def setUp(self):
        """Setup a test client and initialize the database"""
        self.app = create_app('config.py')  # Use the config file
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory DB for testing
        self.app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'  # Override for testing
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Initialize the database (create tables)
        db.create_all()

        # Create a sample user (lecturer)
        self.lecturer = User(username="lecturer1", role="lecturer")
        self.lecturer.set_password("password123")
        db.session.add(self.lecturer)
        db.session.commit()

        # Generate a JWT for the lecturer
        self.token = create_access_token(identity=self.lecturer.id)

    def tearDown(self):
        """Tear down the database after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_submit_results(self):
        """Test submitting results for students"""
        data = {
            "course_code": "CS101",
            "course_title": "Introduction to Computer Science",
            "level": "100",
            "course_unit": 3,
            "semester_name": "First",
            "session": "2023/2024",
            "faculty": "Physical Science",
            "department": "Computer Science",
            "lecturers": [self.lecturer.id], 
            "results": [
                { 
                    "student_name": "Ali Joe",
                    "registration_number": "2021-001",
                    "ca_score": 20,
                    "exam_score": 70,
                    "total_score": 90,
                    "grade": "A"
                },
                {
                    "student_name": "James Bush",
                    "registration_number": "2021-002",
                    "ca_score": 15,
                    "exam_score": 60,
                    "total_score": 75,
                    "grade": "B"
                }
            ]
        }

        response = self.client.post(
            '/submit_results',
            json=data,
            headers={'Authorization': f'Bearer {self.token}'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Results submitted successfully', response.get_json().get('message'))

        # Check that the course and students were added correctly
        course = Course.query.filter_by(code="CS101").first()
        self.assertIsNotNone(course)
        self.assertEqual(course.title, "Introduction to Computer Science")

        student1 = Student.query.filter_by(registration_number="2021-001").first()
        student2 = Student.query.filter_by(registration_number="2021-002").first()
        self.assertIsNotNone(student1)
        self.assertIsNotNone(student2)
        self.assertEqual(student1.name, "Ali Joe")
        self.assertEqual(student2.name, "James Bush")

        # Check that the results were added correctly
        result1 = Result.query.filter_by(student_id=student1.id, course_id=course.id).first()
        result2 = Result.query.filter_by(student_id=student2.id, course_id=course.id).first()
        self.assertEqual(result1.grade, "A")
        self.assertEqual(result2.grade, "B")

    def test_submit_results_invalid_token(self):
        """Test submitting results with an invalid JWT token"""
        data = {
            "course_code": "CS101",
            "course_title": "Introduction to Computer Science",
            "level": "100",
            "course_unit": 3,
            "semester_name": "First",
            "session": "2023/2024",
            "faculty": "Physical Science",
            "department": "Computer Science",
            "lecturers": [self.lecturer.id],
            "results": [
                {
                    "student_name": "Ali Joe",
                    "registration_number": "2021-001",
                    "ca_score": 20,
                    "exam_score": 70,
                    "total_score": 90,
                    "grade": "A"
                }
            ]
        }

        # Make the POST request to submit results with an invalid JWT token
        response = self.client.post(
            '/submit_results',
            json=data,
            headers={'Authorization': 'Bearer invalid_token'}
        )

        # Assert the response status
        self.assertEqual(response.status_code, 401)
        self.assertIn('Invalid token', response.get_json().get('msg'))

if __name__ == '__main__':
    unittest.main()
