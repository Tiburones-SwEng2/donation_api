from flask import Flask
from flasgger import Swagger
from flask_pymongo import PyMongo
from flask_cors import CORS
import os
from dotenv import load_dotenv

mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/donationsdb")
    app.config["UPLOAD_FOLDER"] = "uploads"
    CORS(app)
    mongo.init_app(app)
    Swagger(app)
    CORS(app)

    # Importar y registrar rutas
    from app.routes.donation_routes import donation_bp
    app.register_blueprint(donation_bp, url_prefix="/api")

    return app