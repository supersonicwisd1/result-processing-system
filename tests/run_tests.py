import unittest
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all test modules
from tests.test_auth import TestAuth
from tests.test_results import TestResults
from tests.test_student_results import TestStudentResults

if __name__ == '__main__':
    unittest.main() 