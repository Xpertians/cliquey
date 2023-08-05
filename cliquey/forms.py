from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class ProfileForm(FlaskForm):
    contact_info = StringField('Contact Info', validators=[DataRequired()])
    emails = StringField('Emails', validators=[DataRequired()])
    phones = StringField('Phones', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    urls = StringField('URLs', validators=[DataRequired()])
    submit = SubmitField('Save')
