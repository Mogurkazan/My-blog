from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from dotenv import load_dotenv
import os
import cloudinary

# Cargar variables de entorno desde el archivo .env
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///mi_blog.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'another-super-secret-key')
    app.config['DEEPL_API_KEY'] = os.getenv('DEEPL_API_KEY')

    configure_extensions(app)
    configure_blueprints(app)
    configure_cloudinary()

    return app

def configure_extensions(app):
    """Configura las extensiones de Flask."""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # Nombre de la vista de login
    csrf.init_app(app)

def configure_blueprints(app):
    """Registra los blueprints de la aplicación."""
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

def configure_cloudinary():
    """Configura Cloudinary con las variables de entorno."""
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )

from . import models
