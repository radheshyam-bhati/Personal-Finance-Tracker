from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DecimalField, DateField, TextAreaField, BooleanField, HiddenField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional, ValidationError
from app.models import User, Category

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Log In')

class SignupForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('An account with this email already exists.')

class TransactionForm(FlaskForm):
    type = SelectField('Type', choices=[('income', 'Income'), ('expense', 'Expense')], validators=[DataRequired()])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    description = StringField('Description', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Transaction')
    
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super().__init__(*args, **kwargs)
        if user_id:
            self.category.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=user_id).order_by(Category.name).all()]

class ImportForm(FlaskForm):
    csv_file = FileField('CSV File', validators=[DataRequired()])
    submit = SubmitField('Import')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save Category')

class CategoryRuleForm(FlaskForm):
    keyword = StringField('Keyword', validators=[DataRequired(), Length(max=255)])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Rule')
    
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super().__init__(*args, **kwargs)
        if user_id:
            self.category.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=user_id).order_by(Category.name).all()]

class GoalForm(FlaskForm):
    name = StringField('Goal Name', validators=[DataRequired(), Length(max=255)])
    target_amount = DecimalField('Target Amount', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    start_date = DateField('Start Date', validators=[DataRequired()], format='%Y-%m-%d')
    target_date = DateField('Target Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Save Goal')
    
    def validate_target_date(self, field):
        if self.start_date.data and field.data <= self.start_date.data:
            raise ValidationError('Target date must be after start date.')

class TransactionFilterForm(FlaskForm):
    type = SelectField('Type', choices=[('', 'All'), ('income', 'Income'), ('expense', 'Expense')], validators=[Optional()])
    category = SelectField('Category', coerce=int, validators=[Optional()])
    start_date = DateField('From Date', validators=[Optional()], format='%Y-%m-%d')
    end_date = DateField('To Date', validators=[Optional()], format='%Y-%m-%d')
    min_amount = DecimalField('Min Amount', validators=[Optional(), NumberRange(min=0)], places=2)
    max_amount = DecimalField('Max Amount', validators=[Optional(), NumberRange(min=0)], places=2)
    search = StringField('Search Description', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Filter')
    
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super().__init__(*args, **kwargs)
        if user_id:
            self.category.choices = [(0, 'All Categories')] + [(c.id, c.name) for c in Category.query.filter_by(user_id=user_id).order_by(Category.name).all()]