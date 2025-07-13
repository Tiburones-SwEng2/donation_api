from app import create_app
from flask_jwt_extended import JWTManager

app = create_app()
app.config["JWT_SECRET_KEY"] = "lkhjap8gy2p 03kt"
jwt = JWTManager(app)

if __name__ == "__main__":
    app.run(debug=True)