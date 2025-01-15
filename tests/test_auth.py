from .base import BaseTestCase
import json

class TestAuth(BaseTestCase):
    def test_register_user(self):
        response = self.client.post('/register', json={
            'username': 'new_user',
            'password': 'password123',
            'role': 'lecturer'
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('User registered successfully', response.json['message'])

    def test_login_success(self):
        response = self.client.post('/login', json={
            'username': 'test_hod',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', response.json)

    def test_login_invalid_credentials(self):
        response = self.client.post('/login', json={
            'username': 'test_hod',
            'password': 'wrong_password'
        })
        self.assertEqual(response.status_code, 401) 