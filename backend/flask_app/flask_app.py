from flask import Flask, redirect
from common.extensions import db, bcrypt
from flask_app.routes.auth import auth_bp
from flask_app.routes.user import user_bp
from flask_app.routes.admin import admin_bp
from flask_app.routes.api import api_bp
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "flask_app", "static"),
    static_url_path="/static",
    template_folder=os.path.join(BASE_DIR, "flask_app", "templates")
)

# Config (same as your .env or config file)
db_path = os.path.join(BASE_DIR, "lingolizard.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
print("[DEBUG] Using DB:", db_path)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

# Init extensions
db.init_app(app)
bcrypt.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)

@app.route("/")
def index():
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
