from backend.common import app
from backend.flask_app.routes.auth import auth_bp
from backend.flask_app.routes.user import user_bp
from backend.flask_app.routes.admin import admin_bp
from flask import redirect

# Register routes
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)

@app.route("/")
def index():
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)