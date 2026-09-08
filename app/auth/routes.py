from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app import db, oauth
from app.models import User, Category, CategoryRule
from app.forms import LoginForm, SignupForm

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            session.permanent = True
            next_page = request.args.get('next')
            flash('Welcome back!', 'success')
            return redirect(next_page or url_for('main.dashboard'))

        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/signup.html', form=form)

        user = User(email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        Category.seed_default_categories(user.id)
        CategoryRule.seed_default_rules(user.id)

        db.session.commit()

        login_user(user, remember=True)
        session.permanent = True

        flash('Account created successfully! Welcome to Finance Tracker.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/signup.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')


@auth_bp.route('/login/google')
def login_google():
    redirect_uri = url_for('auth.auth_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/auth/google')
def auth_google():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if user_info:
        email = user_info.get('email').lower().strip()
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create a new user without a password
            user = User(email=email)
            db.session.add(user)
            db.session.flush()
            
            Category.seed_default_categories(user.id)
            CategoryRule.seed_default_rules(user.id)
            
            db.session.commit()
            
        login_user(user, remember=True)
        session.permanent = True
        flash('Successfully logged in with Google.', 'success')
        return redirect(url_for('main.dashboard'))
        
    flash('Google login failed.', 'danger')
    return redirect(url_for('auth.login'))