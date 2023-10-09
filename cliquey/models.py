from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import uuid
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, default=str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    invitation_code = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default="user")
    profiles = db.relationship('Profile', back_populates='user')

    def is_admin(self):
        return self.role == "admin"

    def generate_invitation_code(self, expiration_days=30):
        """Generate a new invitation code with optional expiration."""
        code = secrets.token_hex(8)  # Generate an 8-byte hex token
        expiration = datetime.utcnow() + timedelta(days=expiration_days)
        invitation_code = InvitationCode(code=code, generator_id=self.id, expiration_date=expiration)
        db.session.add(invitation_code)
        db.session.commit()
        return code

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, default=str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='profiles')
    name = db.Column(db.String(100), nullable=False)  # Name for the profile
    phone = db.Column(db.String(20))
    linkedin = db.Column(db.String(200))
    bio = db.Column(db.String(300))
    visit_count = db.Column(db.Integer, default=0)  # To track the number of profile visits

class InvitationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    generator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
