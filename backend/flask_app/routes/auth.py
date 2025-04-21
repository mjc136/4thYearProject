from flask import Blueprint, render_template, request, redirect, session
from backend.models import db, User
from backend.common.extensions import bcrypt
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__, template_folder="templates")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        language = request.form["language"]

        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Username already exists")

        user = User(username=username, password=password, language=language)
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            username = request.form["username"]
            password = request.form["password"]
            
            logger.info(f"Login attempt for user: {username}")
            user = User.query.filter_by(username=username).first()

            if user and bcrypt.check_password_hash(user.password, password):
                session["user_id"] = user.id
                logger.info(f"User {username} logged in successfully")
                return redirect("/profile")
                
            logger.warning(f"Failed login attempt for user: {username}")
            return render_template("login.html", error="Invalid credentials")
        except Exception as e:
            logger.error(f"Login error: {e}")
            return render_template("login.html", error=f"System error: {str(e)}")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
