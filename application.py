import os
import json
import requests
from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from werkzeug.security import generate_password_hash, check_password_hash

from database import db, engine
from models import User

app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(username):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(username)

@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', current_user=current_user)

@app.route("/register")
def register():
    return render_template('register.html')

@app.route("/register", methods=['POST'])
def register_post():
    username = request.form.get('username')
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    # if a user is found, we want to redirect back to signup page so user can try again
    if user:
        flash('Email address already exists')
        return redirect(url_for('register'))

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(username=username, email=email, name=name, 
        password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.add(new_user)
    db.commit()

    # when we add the user to the database, we will redirect to the login route
    return redirect(url_for('login'))

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/login", methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(username=username).first()
    
    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('index'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/search", methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'GET':
        return render_template("error.html", message="Please submit the form instead.")
    else:
        search_term = str(request.form.get('search_term')).lower()    
        
        query_book = f"SELECT * FROM books WHERE LOWER(isbn) LIKE '%{search_term}%' " \
                        f"OR LOWER(title) LIKE '%{search_term}%' "
        query_author = "SELECT * FROM books WHERE EXISTS (SELECT FROM " \
                        f"unnest(author_names) elem WHERE LOWER(elem) LIKE '%{search_term}%') "

        rs_book = db.execute(query_book)
        results = rs_book.fetchall()

        rs_author = db.execute(query_author)
        results += rs_author.fetchall()

        return render_template('search.html', current_user=current_user, results=results)


@app.route("/book/<isbn>", methods=['GET', 'POST'])
@login_required
def book(isbn):
    if request.method == 'POST':
        rating_review = int(request.form.get('rating'))
        text_review = request.form.get('review')
        review_insert = "INSERT INTO reviews (reviewer, isbn, rating, review) " \
            f"VALUES('{current_user.username}', '{isbn}', {rating_review}, '{text_review}')"
        db.execute(review_insert)
        db.commit()
        return redirect(url_for('book', isbn=isbn))
    
    query_book = f"SELECT * FROM books WHERE isbn = '{isbn}'"
    query_review = f"SELECT * FROM reviews WHERE isbn = '{isbn}'"
    query_me = f"SELECT * FROM reviews WHERE reviewer = '{current_user.username}' AND isbn = '{isbn}'"

    bk = db.execute(query_book)
    book = bk.fetchone()

    rv = db.execute(query_review)
    reviews = rv.fetchall()

    mr = db.execute(query_me)
    my_reviews = mr.fetchall()
    enable_review = False if my_reviews else True

    if book is None:
        return render_template("error.html", message="That book doesn't exist")

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": os.environ['GOODREADS_KEY'], "isbns": book.isbn})
    book_info = res.json()
    rating = book_info['books'][0]['average_rating']
    
    return render_template('book.html', current_user=current_user, book=book, rating=rating, 
        reviews=reviews, enable_review=enable_review)


@app.route("/api/<isbn>", methods=['GET'])
@login_required
def api(isbn):
    query_book = f"SELECT * FROM books WHERE isbn = '{isbn}'"
    query_review = f"SELECT * FROM reviews WHERE isbn = '{isbn}'"

    bk = db.execute(query_book)
    book = bk.fetchone()

    rv = db.execute(query_review)
    reviews = rv.fetchall()

    score = 0
    for rev in reviews:
        score += int(rev['rating'])

    avg_score = -1 if len(reviews) == 0 else score/len(reviews)

    data_set = {
        "title": book['title'],
        "author": book['author_names'],
        "year": book['year'],
        "isbn": book['isbn'],
        "review_count": len(reviews),
        "average_score": avg_score, 
    }

    json_dump = json.dumps(data_set)
    json_object = json.loads(json_dump)

    return json_object