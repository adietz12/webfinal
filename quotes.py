from flask import Flask, render_template, request, make_response, redirect, session, flash
from mongita import MongitaClientDisk
from bson import ObjectId
from passwords import hash_password, check_password
#flask --app quotes --debug run

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# create a mongita client connection
client = MongitaClientDisk()

# open the quotes database
quotes_db = client.quotes_db
session_db = client.session_db
user_db = client.user_db

import uuid
#comment
@app.route("/", methods=["GET"])
@app.route("/main_page", methods=["GET"])
def main_page():
    # Check if the user is logged in
    if "user" not in session:
        # If not logged in, redirect to the login page
        return redirect("/login")
    user = session.get("user")
    # open the quotes collection
    quotes_collection = quotes_db.quotes_collection
    # load the data
    data = list(quotes_collection.find({}))
    for item in data:
        item["_id"] = str(item["_id"])
        item["object"] = ObjectId(item["_id"])
    # Render the main page template
    return render_template("main_page.html", quotes=data, user=user)


@app.route("/quotes", methods=["GET"])
def get_quotes():
    session_id = session.get("session_id")
    user = session.get("user")
    if not session_id:
        return redirect("/login")

    # open the quotes collection
    quotes_collection = quotes_db.quotes_collection
    # load the data
    data = list(quotes_collection.find({}))
    for item in data:
        item["_id"] = str(item["_id"])
        item["object"] = ObjectId(item["_id"])
    # display the data
    html = render_template(
        "quotes.html",
        data=data,
        user=user,
    )
    return make_response(html)


@app.route("/login", methods=["GET"])
def get_login():
    session_id = session.get("session_id")
    print("Pre-login session id = ", session_id)
    if session_id:
        return redirect("/quotes")
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def post_login():
    user = request.form.get("user", "")
    password = request.form.get("password", "")

    # open the user collection
    user_collection = user_db.user_collection
    print("Received login attempt - Username:", user, "Password:", password)  # Debugging statement

    # look for the user
    user_data = user_collection.find_one({"username": user})
    print("User data found:", user_data)  # Debugging statement

    # Check if the user exists and the password matches
    if user_data and check_password(password, user_data["password"], user_data["salt"]):
        # Create session for the user
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id
        session["user"] = user
        print("Session ID:", session_id)  # Add this line
        return redirect("/quotes")
    else:
        print("Login failed")
        return redirect("/login")

@app.route("/register", methods=["GET"])
def get_register():
    session_id =session.get("session_id")
    print("Pre-login session id = ", session_id)
    if session_id:
        return redirect("/quotes")
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def post_register():
    user = request.form.get("user", "")
    password = request.form.get("password", "")

    hashed_password, salt = hash_password(password)

    user_collection=user_db.user_collection
    user_data = {"username":user, "password":hashed_password, "salt":salt}
    user_collection.insert_one(user_data)
    print("User collection after registration:", list(user_collection.find()))

    session_id = str(uuid.uuid4())
    session["session_id"] = session_id
    session["user"] = user

    return redirect("/")

@app.route("/logout", methods=["GET"])
def get_logout():
    # Clear the session data
    session.clear()
    # Redirect the user to the login page
    return redirect("/login")


@app.route("/add", methods=["GET"])
def get_add():
    session_id = session.get("session_id")
    if not session_id:
        return redirect("/login")
    return render_template("add_quote.html")


@app.route("/add", methods=["POST"])
def post_add():
    session_id = session.get("session_id")
    if not session_id:
        return redirect("/login")
    
    # Get the user from the session
    user = session.get("user", "unknown user")
    
    # Get form data
    text = request.form.get("text", "")
    author = request.form.get("author", "")
    date = request.form.get("date", "")
    can_comment = request.form.get("cancomment", False)
    # Check if all required fields are provided
    if text != "" and author != "" and date != "":
        # Open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        # Insert the quote
        quote_data = {"owner": user, "text": text, "author": author, "date": date, "comments":can_comment}
        quotes_collection.insert_one(quote_data)
    
    return redirect("/quotes")


@app.route("/edit/<id>", methods=["GET"])
def get_edit(id=None):
    session_id = session.get("session_id")
    if not session_id:
        return redirect("/login")
    if id:
        # Open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        # Get the item
        data = quotes_collection.find_one({"_id": ObjectId(id)})
        if data:
            data["id"] = str(data["_id"])
            return render_template("edit_quote.html", data=data)
    return redirect("/quotes")


@app.route("/edit", methods=["POST"])
def post_edit():
    session_id = session.get("session_id")
    if not session_id:
        return redirect("/login")
    
    _id = request.form.get("_id", None)
    text = request.form.get("text", "")
    author = request.form.get("author", "")
    if _id:
        # Open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        # Update the values in this particular record
        values = {"$set": {"text": text, "author": author}}
        data = quotes_collection.update_one({"_id": ObjectId(_id)}, values)
    
    return redirect("/quotes")


@app.route("/delete", methods=["GET"])
@app.route("/delete/<id>", methods=["GET"])
def get_delete(id=None):
    session_id = session.get("session_id")
    if not session_id:
        return redirect("/login")
    if id:
        # Open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        # Delete the item
        quotes_collection.delete_one({"_id": ObjectId(id)})
    return redirect("/quotes")
