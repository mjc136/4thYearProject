from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from models import db, User
import os
from dotenv import load_dotenv
from azure.appconfiguration import AzureAppConfigurationClient

app = Flask(__name__)

load_dotenv()
connection_string = os.getenv("AZURE_APP_CONFIG_CONNECTION_STRING")

if connection_string:
    try:
        app_config_client = AzureAppConfigurationClient.from_connection_string(connection_string)
        app.secret_key = app_config_client.get_configuration_setting(key="FLASK_SECRET").value
    except Exception as e:
        print(f"Could not fetch from Azure App Configuration: {e}")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lingolizard.db"
db.init_app(app)
with app.app_context():
    db.create_all()

bcrypt = Bcrypt(app)

# ────── ROUTES ──────

@app.route("/")
def index():
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        language = request.form["language"]
        proficiency = request.form["proficiency"]

        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Username already exists")

        user = User(username=username, password=password, language=language, proficiency=proficiency)
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect("/profile")
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
