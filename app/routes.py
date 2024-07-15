from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies
)
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Post, Comment, db
from .forms import PostForm, RegistrationForm, LoginForm

bp = Blueprint('main', __name__)

@bp.app_context_processor
def inject_user():
    return dict(current_user=current_user)

@bp.route('/')
def home():
    latest_posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    return render_template('index.html', latest_posts=latest_posts)


@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/contact')
def contact():
    return render_template('contact.html')

@bp.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        new_post = Post(
            title=form.title.data,
            content=form.content.data,
            keywords=form.keywords.data,
            user_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('main.user_area'))
    return render_template('new_post.html', form=form)

@bp.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        flash('You are not authorized to edit this post.', 'danger')
        return redirect(url_for('main.user_area'))
    
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.keywords = form.keywords.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('main.user_area'))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.keywords.data = post.keywords
    return render_template('edit_post.html', form=form)

@bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        posts = Post.query.filter(Post.keywords.ilike(f'%{query}%')).all()
    else:
        posts = []
    return render_template('search_results.html', posts=posts)


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(
            email=form.email.data,
            nickname=form.nickname.data,
            password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash('You have successfully registered!', 'success')
        return redirect(url_for('main.login'))
    return render_template('signup.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            access_token = create_access_token(identity={'id': user.id, 'email': user.email, 'nickname': user.nickname})
            refresh_token = create_refresh_token(identity={'id': user.id, 'email': user.email, 'nickname': user.nickname})
            response = redirect(url_for('main.user_area'))
            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)
            return response
        flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    response = redirect(url_for('main.home'))
    unset_jwt_cookies(response)
    flash('You have been logged out!', 'success')
    return response


@bp.route('/user_area')
@login_required
def user_area():
    posts = Post.query.filter_by(user_id=current_user.id).all()
    return render_template('user_area.html', posts=posts)
