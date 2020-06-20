from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from werkzeug.security import generate_password_hash, check_password_hash

from database import db
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

@app.route("/")
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

@app.route("/book", methods=['GET', 'POST'])
def book(isbn):
    if request.method == 'GET':
        return render_template("error.html", message="Please submit the form instead.")
    else:
        # session
        search = request.form.get("search")
        return render_template("book.html", search=search)