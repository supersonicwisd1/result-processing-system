import unittest
from app import create_app, db
from app.models import User, Course, Student, Result, Semester

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test users
        self.hod_user = User(username='test_hod', role='hod')
        self.hod_user.set_password('password')
        
        self.lecturer_user = User(username='test_lecturer', role='lecturer')
        self.lecturer_user.set_password('password')
        
        self.exam_officer = User(username='test_exam_officer', role='exam_officer')
        self.exam_officer.set_password('password')

        db.session.add_all([self.hod_user, self.lecturer_user, self.exam_officer])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_auth_token(self, username='test_hod', password='password'):
        response = self.client.post('/login', json={
            'username': username,
            'password': password
        })
        return response.json['access_token'] 