from .base import BaseTestCase

class TestStudentResults(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Submit test results first
        token = self.get_auth_token('test_lecturer', 'password')
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
        self.client.post(
            '/submit_results',
            headers={'Authorization': f'Bearer {token}'},
            json=self.test_data
        )

    def test_get_results_by_registration(self):
        token = self.get_auth_token('test_hod', 'password')
        response = self.client.get(
            '/get_results_by_registration_number?registration_number=2023/001',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.json) 