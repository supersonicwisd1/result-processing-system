To run
FLASK_APP=app.py FLASK_ENV=development flask run --port 8080 --reload

pip install pytest pytest-cov
pytest --cov=app tests/