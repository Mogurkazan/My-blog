from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mi_blog.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'jhsagdfyut7a4w8hovsdicyuvjdhfuigyv89easrhvbkjdufhugyv 7s `V98Y9S'  # Cambia esto a una clave secreta más segura
    app.config['SECRET_KEY'] = 'bnsdyfg678234bf9sd8fvw34eu7frr3w4fui9ds8f77`WFHTDF7G6H'

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Nombre de la vista de login
    csrf.init_app(app)

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app

from . import models
