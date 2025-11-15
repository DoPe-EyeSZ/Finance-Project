from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def create_app():
    load_dotenv()

    app = Flask(__name__, static_folder="../static", template_folder="templates")
    app.secret_key = os.getenv("secret_key")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///budget.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["SESSION_PERMANENT"] = False
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

    db.init_app(app)

    from app.routes import register_blueprint
    register_blueprint(app)

    return app


