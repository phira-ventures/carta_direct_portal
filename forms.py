from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError, EqualTo, Regexp
import re

def validate_strong_password(form, field):
    """Custom validator for strong password requirements."""
    password = field.data
    if len(password) < 12:
        raise ValidationError('Password must be at least 12 characters long.')
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter.')
    
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one number.')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError('Password must contain at least one special character.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class UpdateStocksForm(FlaskForm):
    user_id = IntegerField('User ID', validators=[DataRequired()])
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=1, max=100)
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    stock_count = IntegerField('Stock Count', validators=[
        DataRequired(),
        NumberRange(min=0, max=10000000, message="Stock count must be between 0 and 10,000,000")
    ])
    submit = SubmitField('Update Stockholder')

class UpdateTotalStocksForm(FlaskForm):
    total_stocks = IntegerField('Total Stocks', validators=[
        DataRequired(), 
        NumberRange(min=1, message="Total stocks must be positive")
    ])
    submit = SubmitField('Update Total Stocks')

class CreateStockholderForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=1, max=100)
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        validate_strong_password
    ])
    stock_count = IntegerField('Initial Stocks', validators=[
        DataRequired(),
        NumberRange(min=0, max=10000000, message="Stock count must be between 0 and 10,000,000")
    ])
    submit = SubmitField('Create Stockholder')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[
        DataRequired()
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        validate_strong_password
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message="Passwords must match")
    ])
    submit = SubmitField('Change Password')

class ResetPasswordForm(FlaskForm):
    """Form for admin to reset user passwords."""
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        validate_strong_password
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('new_password', message="Passwords must match")
    ])
    submit = SubmitField('Reset Password')