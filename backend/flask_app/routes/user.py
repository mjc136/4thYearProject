from flask import Blueprint, render_template, redirect, session
from backend.models import User

user_bp = Blueprint("user", __name__,template_folder="templates")

@user_bp.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)

@user_bp.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("chat.html")
