from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect

db = SQLAlchemy()
bcrypt = Bcrypt()
csrf = CSRFProtect()
