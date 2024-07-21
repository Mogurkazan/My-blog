from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, render_template_string, current_app
import requests
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies
)
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import cloudinary.uploader
from .models import User, Post, Comment, Favorite, db
from .forms import PostForm, RegistrationForm, LoginForm, CommentForm, LogoutForm, ProfileImageForm

bp = Blueprint('main', __name__)

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        profile_image_url = None

        if form.profile_image.data:
            upload_result = cloudinary.uploader.upload(form.profile_image.data)
            profile_image_url = upload_result.get('secure_url')

        new_user = User(
            email=form.email.data,
            nickname=form.nickname.data,
            password_hash=hashed_password,
            profile_image=profile_image_url
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
            flash('Login successful.', 'success')
            return redirect(url_for('main.user_area'))
        flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))

@bp.route('/')
def home():
    latest_posts = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    logout_form = LogoutForm()
    return render_template('index.html', latest_posts=latest_posts, logout_form=logout_form)

@bp.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        image_url = None
        if form.image.data:
            upload_result = cloudinary.uploader.upload(form.image.data)
            image_url = upload_result.get('url')
        
        new_post = Post(
            title=form.title.data,
            content=form.content.data,
            keywords=form.keywords.data,
            image_url=image_url,  # Guardar la URL de la imagen
            user_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.user_area'))
    logout_form = LogoutForm()
    return render_template('new_post.html', form=form, logout_form=logout_form)

@bp.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        flash('You do not have permission to edit this post.', 'danger')
        return redirect(url_for('main.user_area'))
    
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.keywords = form.keywords.data
        if form.image.data:
            upload_result = cloudinary.uploader.upload(form.image.data)
            post.image_url = upload_result.get('url')
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('main.user_area'))
    
    if request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.keywords.data = post.keywords
    
    logout_form = LogoutForm()
    return render_template('edit_post.html', form=form, logout_form=logout_form)

@bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    logout_form = LogoutForm()
    favorite_form = LogoutForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        add_comment(post_id, form.content.data)
    comments = get_comments(post_id)
    is_favorite = check_favorite_status(post)
    return render_template('view_post.html', post=post, comments=comments, form=form, logout_form=logout_form, is_favorite=is_favorite, favorite_form=favorite_form)

#########translate#############

@bp.route('/translate_post_page/<int:post_id>', methods=['POST'])
def translate_post_page(post_id):
    language = request.form.get('language')
    content = request.form.get('content')

    if language and content:
        api_key = current_app.config['DEEPL_API_KEY']
        url = "https://api-free.deepl.com/v2/translate"
        params = {
            'auth_key': api_key,
            'text': content,
            'target_lang': language.upper()
        }

        response = requests.post(url, data=params)

        if response.status_code == 200:
            translated_text = response.json()['translations'][0]['text']
            return render_template('translated_post.html', translated_text=translated_text, post_id=post_id)
        else:
            flash('Translation failed.', 'danger')
            return redirect(url_for('main.view_post', post_id=post_id))

    flash('Missing data for translation.', 'danger')
    return redirect(url_for('main.view_post', post_id=post_id))



#########comments##########

def add_comment(post_id, content):
    new_comment = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post_id
    )
    db.session.add(new_comment)
    db.session.commit()
    flash('Your comment has been added!', 'success')

def get_comments(post_id):
    return Comment.query.filter_by(post_id=post_id).order_by(Comment.date_posted.desc()).all()

########Favorites###################

def check_favorite_status(post):
    return current_user.is_authenticated and post in current_user.favorites

@bp.route('/add_favorite/<int:post_id>', methods=['POST'])
@login_required
def add_favorite(post_id):
    post = Post.query.get_or_404(post_id)
    if post not in current_user.favorites:
        favorite = Favorite(user_id=current_user.id, post_id=post_id)
        db.session.add(favorite)
        db.session.commit()
        flash('Post added to favorites!', 'success')
    favorite_html = render_favorite_button(post)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Check if the request is AJAX
        return jsonify(favorite_html=favorite_html)
    else:
        return redirect(url_for('main.view_post', post_id=post_id))

@bp.route('/remove_favorite/<int:post_id>', methods=['POST'])
@login_required
def remove_favorite(post_id):
    post = Post.query.get_or_404(post_id)
    favorite = Favorite.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash('Post removed from favorites!', 'success')
    favorite_html = render_favorite_button(post)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Check if the request is AJAX
        return jsonify(favorite_html=favorite_html)
    else:
        return redirect(url_for('main.favorites'))

@bp.route('/favorites')
@login_required
def favorites():
    favorites = Post.query.join(Favorite, (Favorite.post_id == Post.id)).filter(Favorite.user_id == current_user.id).all()
    logout_form = LogoutForm()
    favorite_form = LogoutForm()
    return render_template('favorites.html', favorites=favorites, logout_form=logout_form, favorite_form=favorite_form)

def render_favorite_button(post):
    is_favorite = check_favorite_status(post)
    favorite_form = LogoutForm()
    return render_template_string("""
        <form id="favorite-form" action="{{ url_for('main.' + ('remove_favorite' if is_favorite else 'add_favorite'), post_id=post.id) }}" method="POST">
            {{ favorite_form.hidden_tag() }}
            <button type="submit" class="btn btn-warning">
                {{ 'Remove from Favorites' if is_favorite else 'Add to Favorites' }}
            </button>
        </form>
    """, post=post, is_favorite=is_favorite, favorite_form=favorite_form)

###########Private Area#################################

@bp.route('/user_area', methods=['GET', 'POST'])
@login_required
def user_area():
    posts = Post.query.filter_by(user_id=current_user.id).all()
    logout_form = LogoutForm()
    profile_image_form = ProfileImageForm()

    if profile_image_form.validate_on_submit():
        if profile_image_form.profile_image.data:
            upload_result = cloudinary.uploader.upload(profile_image_form.profile_image.data)
            current_user.profile_image = upload_result.get('url')
            db.session.commit()
            flash('Profile image updated successfully.', 'success')
            return redirect(url_for('main.user_area'))

    return render_template('user_area.html', posts=posts, logout_form=logout_form, profile_image_form=profile_image_form)

@bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        posts = Post.query.filter(Post.keywords.ilike(f'%{query}%')).all()
    else:
        posts = []
    logout_form = LogoutForm()
    return render_template('search_results.html', posts=posts, query=query, logout_form=logout_form)
