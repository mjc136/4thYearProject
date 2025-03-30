from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import check_password_hash
from backend.models import db, User
from flask_bcrypt import Bcrypt

auth_bp = Blueprint("auth", __name__, template_folder="templates")

bcrypt = Bcrypt()

@auth_bp.route("/register", methods=["GET", "POST"])
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

@auth_bp.route("/login", methods=["GET", "POST"])
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

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
