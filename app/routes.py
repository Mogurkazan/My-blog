from flask import Blueprint, render_template
from .forms import PostForm

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/contact')
def contact():
    return render_template('contact.html')

@bp.route('/new_post', methods=['GET', 'POST'])
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        # Aquí puedes añadir lógica para guardar el post en la base de datos
        return redirect(url_for('main.home'))
    return render_template('new_post.html', form=form)
