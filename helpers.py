from flask import session, redirect, url_for, flash
from functools import wraps
import sqlite3
import requests
import xmltodict
   
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('username') is None:
            return redirect("login")
        return f(*args, **kwargs)
    return decorated_function


def open_db():
    # Open db connection
    connection = sqlite3.connect("bgcomp.db")
    # Create 'dictionary cursor'. Just easier to work with than tuples!
    connection.row_factory = sqlite3.Row
    db = connection.cursor()
    return connection, db


def close_db(connection, db):
    db.close()
    connection.close()
    return


def validate_username(username):
    # Check username length
    if len(username) < 3 or len(username) > 20:
      return True
    
    # Check username only contains alphanumeric characters or spaces
    user_no_space = username.replace(" ", "")
    if any(not c.isalnum() for c in user_no_space):
      return True
    
    # Check username does not start or end with a space
    if username[0] == " " or username[-1] == " ":
      return True
    
    return False


def validate_password(password, confirm):
    # Check password length
    if len(password) < 8 or len(password) > 50:
      return True
    
    # Check password contains allowed characters
    chars = "*:,'\""
    for c in chars:
       if c in password:
          return True
    
    # Check password and confirmation match
    if password != confirm:
      flash("Password and confirmation do not match")
      return redirect(url_for("register"))
    
    return False

def get_user_id(username):
  connection, db = open_db()
  username = session['username']
  statement = "SELECT id FROM users WHERE username = (?)"
  userId_rows = db.execute(statement, (username,)).fetchall()
  close_db(connection, db)
  for row in userId_rows:
    userId = row['id']
  return userId

def add_gamecache(gameId):
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
      try:
        name = parsed['items']['item']['name'][0]['@value']
      except KeyError:
        name = parsed['items']['item']['name']['@value']

      #  Insert gameid, gamename and image into database to reduce API calls for collection page
      insert_statement = "INSERT INTO gamecache (gameid, name, image) VALUES (?, ?, ?)"
      data = (gameId, name, image)
      cache_db.execute(insert_statement, data)
      cache_connection.commit()
      close_db(cache_connection, cache_db)