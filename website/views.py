from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Post, User, Comment, Like, Book
from . import db

from sqlalchemy import desc
from sqlalchemy.sql.expression import func

views = Blueprint("views", __name__)

@views.route('/')
@views.route('/index.html')
def my_home():
    posts = Post.query.all()[:4]
    books = Book.query.all()[:4]
    try:
        print('ID',current_user.id)
        auth = True
    except:
        auth = False
    return render_template('index.html', auth = auth,posts = posts, books = books)



@views.route('/article/<id>')
def article(id):
    name = Post.query.filter_by(id=id).first().name
    text = Post.query.filter_by(id=id).first().text
    date_created = Post.query.filter_by(id=id).first().date_created
    post = Post.query.filter_by(id=id).first()
    return render_template('article.html', name = name, text = text, date_created = str(date_created)[:10],post=post)

@views.route("/books.html")
def books():
    books = Book.query.all()
    return render_template('books.html', books=books)

@views.route('/show_all')
def show_all():
    print(str(Post.query.all()))
    return """{% for post in Post %}
               <tr>
                  <td>{{ post.text }}</td>
               </tr>
            {% endfor %}"""


@views.route('/<string:page_name>')
def html_page(page_name):
    return render_template(page_name)


@views.route('/submit_form', methods=['POST','GET'])
def submit_form():

    if request.method == 'POST':
        data = request.form.to_dict()
        write_to_csv(data)

        return redirect('/thankyou.html')
    else:
        return 'Something went wrong. Please try again'

def write_to_csv(data):
	with open('database.csv', newline='',mode='a') as database:
		email = data['email']
		subject = data['subject']
		message = data['message']
		csv_writer = csv.writer(database, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		csv_writer.writerow([email,subject,message])


@views.route("/admin")
@login_required
def home():
    posts = Post.query.all()
    books = Book.query.all()
    return render_template("home.html", user=current_user, posts=posts,books=books)


@views.route("/articles.html")
def articles():
    posts = Post.query.all()

    return render_template('articles.html', posts=posts)


@views.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == "POST":
        text = request.form.get('text')
        name = request.form.get('name')

        if not text:
            flash('Post cannot be empty', category='error')
        else:
            post = Post(text=text, name=name, author=current_user.id)
            db.session.add(post)
            db.session.commit()
            flash('Post created!', category='success')
            return redirect(url_for('views.home'))

    return render_template('create_post.html', user=current_user)


@views.route("/add_book", methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == "POST":
        name = request.form.get('name')
        info = request.form.get('info')
        author = request.form.get('author')
        link = request.form.get('link')

        if not name:
            flash('Book cannot be empty', category='error')
        else:
            book = Book(name=name, info=info, author=author, link = link)
            db.session.add(book)
            db.session.commit()
            flash('Book Added!', category='success')
            return redirect(url_for('views.home'))

    return render_template('add_book.html', user=current_user)


@views.route("/delete-post/<id>")
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash("Post does not exist.", category='error')
    elif current_user.id != post.id:
        flash('You do not have permission to delete this post.', category='error')
    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', category='success')

    return redirect(url_for('views.home'))


@views.route("/posts/<username>")
@login_required
def posts(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('views.home'))

    posts = user.posts
    return render_template("posts.html", user=current_user, posts=posts, username=username)


@views.route("/create-comment/<post_id>", methods=['POST'])
def create_comment(post_id):
    text = request.form.get('text')
    username = request.form.get('username')
    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.filter_by(id=post_id)
        if post:
            comment = Comment(
                text=text, author=username, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

    print('works')
    return redirect('/article/'+str(post_id))


@views.route("/delete-comment/<comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()

    if not comment:
        flash('Comment does not exist.', category='error')
    elif current_user.id != comment.author and current_user.id != comment.post.author:
        flash('You do not have permission to delete this comment.', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('views.home'))


@views.route("/like-post/<post_id>", methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id).first()
    like = Like.query.filter_by(
        author=current_user.id, post_id=post_id).first()

    if not post:
        return jsonify({'error': 'Post does not exist.'}, 400)
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    return jsonify({"likes": len(post.likes), "liked": current_user.id in map(lambda x: x.author, post.likes)})
