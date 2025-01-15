from .base import BaseTestCase
from app.models import Result
import json

class TestResults(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create test data
        self.test_data = {
            "course_code": "CS101",
            "course_title": "Introduction to Programming",
            "course_unit": 3,
            "level": "100",
            "faculty": "Science",
            "exam_department": "Computer Science",
            "semester_name": "First",
            "session": "2023/2024",
            "results": [
                {
                    "student_name": "John Doe",
                    "registration_number": "2023/001",
                    "student_department": "Computer Science",
                    "ca_score": 30,
                    "exam_score": 60,
                    "total_score": 90,
                    "grade": "A"
                }
            ]
        }

    def test_submit_results(self):
        token = self.get_auth_token('test_lecturer', 'password')
        response = self.client.post(
            '/submit_results',
            headers={'Authorization': f'Bearer {token}'},
            json=self.test_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Results submitted successfully', response.json['message'])

    def test_get_results_by_course(self):
        # First submit a result
        token = self.get_auth_token('test_lecturer', 'password')
        self.client.post(
            '/submit_results',
            headers={'Authorization': f'Bearer {token}'},
            json=self.test_data
        )

        # Then try to get the results
        response = self.client.post(
            '/get_results_by_course_code',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'course_code': 'CS101',
                'semester_name': 'First',
                'session': '2023/2024'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.json)

    def test_delete_result(self):
        # First submit a result
        token = self.get_auth_token('test_lecturer', 'password')
        response = self.client.post(
            '/submit_results',
            headers={'Authorization': f'Bearer {token}'},
            json=self.test_data
        )

        # Get the result ID (you'll need to modify your submit_results endpoint to return the result ID)
        result = Result.query.first()
        
        # Try to delete the result
        response = self.client.delete(
            '/delete_result',
            headers={'Authorization': f'Bearer {token}'},
            json={'result_id': result.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Result deleted successfully', response.json['message']) 