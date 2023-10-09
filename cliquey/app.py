from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Profile, InvitationCode
from datetime import datetime
from flask_migrate import Migrate
from flask import flash, get_flashed_messages


app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('profiles_list'))
        else:
            return 'Invalid email or password'
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Check the validity of the invitation code
        invitation_code = request.form['invitation_code']
        code_entry = InvitationCode.query.filter_by(code=invitation_code, is_used=False).first()

        if not code_entry or code_entry.expiration_date < datetime.utcnow():
            return "Invalid or expired invitation code"

        hashed_password = generate_password_hash(request.form['password'], method='sha256')
        new_user = User(email=request.form['email'], password=hashed_password, invitation_code=invitation_code)
        db.session.add(new_user)
        db.session.commit()

        code_entry.is_used = True
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/profile/<public_id>')
def public_profile(public_id):
    profile = Profile.query.filter_by(public_id=public_id).first()
    if not profile:
        return "Profile not found", 404

    # Increment the visit count for the profile
    profile.visit_count += 1
    db.session.commit()
    
    return render_template('profile.html', profile=profile)

@app.route('/generate_code', methods=['POST'])
@login_required
def generate_code():
    user = current_user
    if not user.is_admin():
        return "Access denied", 403
    
    code = user.generate_invitation_code()
    return f"Generated code: {code}"


@app.route('/profile/create', methods=['GET', 'POST'])
@login_required
def create_profile():
    if request.method == 'POST':
        profile_name = request.form.get('name')
        phone = request.form.get('phone')
        linkedin = request.form.get('linkedin')
        bio = request.form.get('bio')

        new_profile = Profile(
            user_id=current_user.id,
            name=profile_name,
            phone=phone,
            linkedin=linkedin,
            bio=bio
        )
        db.session.add(new_profile)
        db.session.commit()

        flash('Profile created successfully!')
        return redirect(url_for('profiles_list'))

    return render_template('create_profile.html')

@app.route('/profile/edit/<int:profile_id>', methods=['GET', 'POST'])
@login_required
def edit_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if profile.user_id != current_user.id:
        flash('Unauthorized access!')
        return redirect(url_for('profiles_list'))

    if request.method == 'POST':
        profile.name = request.form.get('name')
        profile.phone = request.form.get('phone')
        profile.linkedin = request.form.get('linkedin')
        profile.bio = request.form.get('bio')

        db.session.commit()

        flash('Profile updated successfully!')
        return redirect(url_for('profiles_list'))

    return render_template('edit_profile.html', profile=profile)

@app.route('/profile/delete/<int:profile_id>', methods=['POST'])
@login_required
def delete_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if profile.user_id != current_user.id:
        flash('Unauthorized access!')
        return redirect(url_for('profiles_list'))

    db.session.delete(profile)
    db.session.commit()

    flash('Profile deleted successfully!')
    return redirect(url_for('profiles_list'))

@app.route('/profiles')
@login_required
def profiles_list():
    profiles = Profile.query.filter_by(user_id=current_user.id).all()
    return render_template('profile_list.html', profiles=profiles)

if __name__ == "__main__":
    app.run(debug=True)
