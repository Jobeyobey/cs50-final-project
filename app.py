from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from helpers import login_required, open_db, close_db, validate_username, validate_password
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import requests
import xmltodict

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

    # Get username from session
    username = session['username']
    print(username)
    return render_template("index.html", username=username)

  # POST
  if request.method == "POST":
    # Get user query
    query = request.form.get("query")

    return render_template("index.html")


@app.route("/collection")
@login_required
def collection():

  # Get userId
  connection, db = open_db()
  username = session['username']
  statement = "SELECT id FROM users WHERE username = (?)"
  userId_rows = db.execute(statement, (username,)).fetchall()
  close_db(connection, db)
  for row in userId_rows:
    userId = row['id']
    
  # Get user's collection
  connection, db = open_db()
  statement = "SELECT gameid FROM collections WHERE userid = (?)"
  collection_rows = db.execute(statement, (userId,)).fetchall()
  user_collection = []
  for row in collection_rows:
    user_collection.append(row['gameid'])
  close_db(connection, db)

  # Get gamenames and thumbs from gamecache
  connection, db = open_db()
  statement = "SELECT name, image FROM gamecache WHERE gameid = (?)"
  length = len(user_collection)
  if length > 1:
    for i in range(1, length):
      statement = statement + " OR gameid = (?)"
  cache_rows = db.execute(statement, user_collection).fetchall()
  close_db(connection, db)
  games = []
  for row in cache_rows:
    games.append({'name': row['name'], 'thumb': row['image']})

  print(games)


  return render_template("collection.html", games=games)


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
  

  
@app.route("/gamepage", methods=["GET", "POST"])
@login_required
def gamepage():
  # Get game id from url
  gameId = int(request.args['id'])

  user = session['username']

  # Get user ID from database
  connection, db = open_db()
  username = session['username']
  userId_statement = (
    "SELECT id FROM users WHERE username = (?)"
  )
  userId_row = db.execute(userId_statement, (username,)).fetchall()
  for row in userId_row:
    userId = row['id']
  close_db(connection, db)

  data = (userId, gameId)

  # Search user collection for game
  connection, db = open_db()
  # Check if gameid is in collection
  userCollection_statement = (
    "SELECT gameid FROM collections WHERE userid = (?) AND gameid = (?)"
  )
  userCollection = db.execute(userCollection_statement, data).fetchall()
  close_db(connection, db)

  if userCollection == []:
    inCollection = False
  else:
    inCollection = True

  if request.method == "POST":
    # OPEN CONNECTIONS FOR ADD/REMOVE GAME FROM USER COLLECTION
    user_connection, user_db = open_db()

    # If game is not in collection, add it. Else, delete it.
    if userCollection:
      delete_statement = (
        "DELETE FROM collections WHERE userid = (?) AND gameid = (?)"
      )
      user_db.execute(delete_statement, data)
      user_connection.commit()
      close_db(user_connection, user_db)
    else:
      add_statement = (
        "INSERT INTO collections (userid, gameid) VALUES (?, ?)"
      )
      user_db.execute(add_statement, data)
      user_connection.commit()
      close_db(user_connection, user_db)

      # Check if game already exists in gamecache
      cache_connection, cache_db = open_db()
      statement = "SELECT gameid FROM gamecache WHERE gameid = (?)"
      response = cache_db.execute(statement, (gameId,)).fetchall()
      # If game doesn't exist in gamecache, update gamecache with new game
      if response == []:
        #  Get thumbnail and gamename from BGG API
        url = "https://boardgamegeek.com/xmlapi2/thing?id=" + str(gameId)
        response = requests.get(url)
        parsed = xmltodict.parse(response.content)
        image = parsed['items']['item']['thumbnail']
        name = parsed['items']['item']['name'][0]['@value']

        #  Insert gameid, gamename and image into database to reduce API calls for collection page
        insert_statement = "INSERT INTO gamecache (gameid, name, image) VALUES (?, ?, ?)"
        data = (gameId, name, image)
        cache_db.execute(insert_statement, data)
        cache_connection.commit()
        close_db(cache_connection, cache_db)

    # Create url for redirecting back to page for refresh
    tempUrl = "/gamepage?id=" + str(gameId)

    return redirect(tempUrl)

  if request.method == "GET":

    return render_template("gamepage.html", gameId=gameId, inCollection=inCollection)



if __name__ == "__main__":
  app.run()