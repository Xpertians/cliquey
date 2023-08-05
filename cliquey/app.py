from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)

# ... (previous code)

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    # Add the 'profiles' relationship to the User model
    profiles = db.relationship('PublicProfile', back_populates='user')

# ... (previous code)

class PublicProfile(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_info = db.Column(db.String(100), nullable=False)
    emails = db.Column(db.String(200))
    phones = db.Column(db.String(100))
    description = db.Column(db.Text)
    urls = db.Column(db.String(200))

    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='profiles')

    ratings_sum = Column(Integer, default=0)   # To store the sum of all ratings
    num_ratings = Column(Integer, default=0)   # To store the number of ratings
    average_rating = Column(Float, default=0)  # To store the average rating

# ... (Rest of the code remains the same)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            flash('Login successful', 'success')
            return redirect(url_for('profile_list'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/profile/create', methods=['GET','POST'])
def create_profile():
    if 'user_id' not in session:
        flash('Please login to create a profile', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        contact_info = request.form['contact_info']
        new_profile = PublicProfile(user_id=user_id, contact_info=contact_info)
        db.session.add(new_profile)
        db.session.commit()
        flash('Profile created successfully', 'success')
        return redirect(url_for('profile_list'))

    return render_template('profile_form.html', action='Create', form_data=None)


@app.route('/profile/<string:profile_id>/edit', methods=['GET', 'POST'])
def edit_profile(profile_id):
    profile = PublicProfile.query.filter_by(id=profile_id).first()

    if not profile:
        flash('Profile not found.', 'danger')
        return redirect(url_for('profile_list'))

    if profile.user_id != session['user_id']:
        flash('You do not have permission to edit this profile.', 'danger')
        return redirect(url_for('profile_list'))

    if request.method == 'POST':
        # Update the profile information in the database
        profile.contact_info = request.form.get('contact_info')
        profile.emails = request.form.get('emails')
        profile.phones = request.form.get('phones')
        profile.description = request.form.get('description')
        profile.urls = request.form.get('urls')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile_details', profile_id=profile_id))

    # Render the template with form_data
    return render_template('profile_form.html', title='Edit Profile', form_data=profile)




@app.route('/profile/<string:profile_id>/delete', methods=['POST'])
def delete_profile(profile_id):
    if 'user_id' not in session:
        flash('Please login to delete profiles', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    profile = PublicProfile.query.get_or_404(profile_id)

    if profile.user_id != user_id:
        flash("You can't delete profiles that don't belong to you.", 'error')
        return redirect(url_for('profile_list'))

    db.session.delete(profile)
    db.session.commit()
    flash('Profile deleted successfully!', 'success')
    return redirect(url_for('profile_list'))


@app.route('/profile/<string:profile_id>/rate', methods=['POST'])
def rate_profile(profile_id):
    if 'user_id' not in session:
        flash('Please login to rate profiles', 'error')
        return redirect(url_for('login'))


    profile = PublicProfile.query.get_or_404(profile_id)
    if profile.user_id == profile_id:
        flash('You cannot rate your own profile', 'error')
        return redirect(url_for('profile_details', profile_id=profile_id))

    new_rating = int(request.form.get('rating'))
    # Update the sum and count of ratings for the profile in the database
    profile.ratings_sum += new_rating
    profile.num_ratings += 1
    profile.average_rating = profile.ratings_sum / profile.num_ratings
    db.session.commit()

    flash('Rating submitted successfully', 'success')
    return redirect(url_for('profile_details', profile_id=profile_id))

@app.route('/profile/<string:profile_id>', methods=['GET'])
def profile_details(profile_id):
    if 'user_id' not in session:
        flash('Please login to view profiles', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    profile = PublicProfile.query.get_or_404(profile_id)

    return render_template('profile_details.html', profile=profile, user=user)


@app.route('/profile', methods=['GET', 'POST'])
def profile_list():
    if 'user_id' not in session:
        flash('Please login to view profiles', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        search_term = request.form.get('search_term', '').strip()
        profiles = PublicProfile.query.filter(PublicProfile.contact_info.contains(search_term)).all()
    else:
        profiles = PublicProfile.query.all()
    # Sort the profiles by rating in descending order
    profiles = sorted(profiles, key=lambda profile: profile.rating, reverse=True)
    return render_template('profile_list.html', profiles=profiles, user=user)



with app.app_context():
    db.create_all()
if __name__ == '__main__':
    app.run(debug=True)
