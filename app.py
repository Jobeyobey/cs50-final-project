from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from helpers import login_required, open_db, close_db, validate_username, validate_password
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3

app = Flask(__name__)

# Session configuration
app.config['SECRET_KEY'] = os.urandom(12)
app.config['SESSION_TYPE'] = "filesystem"
Session(app)

@app.route("/signout")
def signout():
  session.clear()
  return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():

  # POST
  if request.method == "POST":

    # Connect to sqlite database
    connection, db = open_db()

    # Prepare insert statement and data
    username = request.form.get("username")
    password = request.form.get("password")
    insert_statement = (
      "SELECT username, hash FROM users WHERE username = ?"
    )

    # Insert data
    user = db.execute(insert_statement, (username,)).fetchall()

    # Check user exists
    if user == []:
      flash("Username or password incorrect")
      return redirect(url_for("login"))
    
    # Check password is correct
    if not check_password_hash(user[0]['hash'], password):
      flash("Username or password incorrect")
      return redirect(url_for("login"))

    # Close database cursor and connection
    close_db(connection, db)

    session['username'] = username
    flash("Logged in")

    return redirect("/")

  # GET
  if request.method == "GET":

    # If user is logged in, go to index
    if session.get('username') is not None:
      return redirect(url_for("index"))
    
    return render_template("login.html")
  

@app.route("/register", methods=["GET", "POST"])
def register():

  # POST
  if request.method == "POST":

    # Connect to sqlite database
    connection, db = open_db()

    # Retrieve user/password from registration form
    username = request.form.get("username")
    password = request.form.get("password")

    # Check username and password are valid
    if validate_username(username):
      flash("Username must be 3-20 characters. Alphanumeric and spaces only. Must not start or end with a space.")
      return redirect(url_for("register"))
    
    if validate_password(password, request.form.get("confirm")):
      flash("Password must be 8-50 characters. Cannot contain * : ' \"")
      return redirect(url_for("register"))

    # Check if username is taken
    select_statement = (
      "SELECT username FROM users WHERE username = (?)"
    )
    user_check = db.execute(select_statement, (username,)).fetchall()
    if user_check:
      db.close()
      connection.close()
      flash("Username taken")
      return redirect(url_for("register"))
    
    # Generate hash and data to insert into db
    hash = generate_password_hash(password)
    data = (username, hash)

    # Insert user into database
    insert_statement = (
      "INSERT INTO users (username, hash) VALUES (?, ?)"
    )
    db.execute(insert_statement, data)

    # Commit to and close database
    connection.commit()
    close_db(connection, db)

    session['username'] = username

    return redirect("/login")
  
  # GET
  return render_template("register.html")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
  # GET
  if request.method == "GET":
    return render_template("index.html")

  # POST
  if request.method == "POST":
    # Get user query
    query = request.form.get("query")

    return render_template("index.html")


@app.route("/collection")
@login_required
def collection():

  return render_template("collection.html")


@app.route("/playlog")
@login_required
def playlog():

  return render_template("playlog.html")


@app.route("/friends")
@login_required
def friends():
  
  return render_template("friends.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
  #POST
  if request.method == "POST":
    # Get user query
    query = request.form.get("query")
    print(query)
    
    return render_template("search.html", query=query)
  
  #GET
  redirect("/")
  

  
@app.route("/gamepage")
@login_required
def gamepage():
  # Get requested game id from URL query
  id = request.args['id']

  return render_template("gamepage.html", id=id)



if __name__ == "__main__":
  app.run()