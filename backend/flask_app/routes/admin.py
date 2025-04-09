from flask import Blueprint, render_template, redirect, session, request
from models import User
from common.extensions import db

admin_bp = Blueprint("admin", __name__, template_folder="templates")

@admin_bp.route("/admin", methods=["GET", "POST"])
def admin_tools():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])
    if not user or not user.admin:
        return "Access denied", 403

    if request.method == "POST":
        new_language = request.form.get("language")
        new_proficiency = request.form.get("proficiency")

        if new_language:
            user.language = new_language.lower()
        if new_proficiency:
            user.proficiency = new_proficiency.lower()

        db.session.commit()
        return redirect("/admin")

    return render_template("admin.html", user=user)
