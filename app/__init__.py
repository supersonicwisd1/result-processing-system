# flask-app/app/__init__.py
import os
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from config import DevelopmentConfig, ProductionConfig, TestingConfig
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_migrate import Migrate  

db = SQLAlchemy()

mail = Mail()

def create_app():
    app = Flask(__name__)

    migrate = Migrate(app, db)

    CORS(app)
    limiter = Limiter(get_remote_address, app=app, storage_uri="redis://localhost:6379",
  storage_options={"socket_connect_timeout": 30},
  strategy="fixed-window")

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        app.config.from_object(ProductionConfig)
    elif env == 'testing':
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    db.init_app(app)
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_IDENTITY_CLAIM'] = 'sub'
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ["access", "refresh"]

    # Set up Flask-Mail configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')  # SMTP server address (use your email service provider's SMTP)
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))  # SMTP port
    app.config['MAIL_USE_TLS'] = True  # Use TLS encryption
    app.config['MAIL_USE_SSL'] = False  # Disable SSL
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Your email address
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Your email password

    # Initialize mail with the app
    mail.init_app(app)
    
    # Rest of your configurations...
    jwt = JWTManager(app)
    
    # Add this JWT callback
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return str(user) if isinstance(user, int) else user

    # Initialize API with app directly
    from app.routes import api
    api.init_app(app)

    with app.app_context():
        db.create_all()

    return app