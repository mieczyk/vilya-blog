import logging
from functools import wraps

from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for, Response)
from flask_cors import CORS

# Flask app's configuration
app = Flask(__name__)

# Make the app vulnerable by allowing CORS (Cross Origin Resource Sharing)
# for all domains on all routes.
CORS(app, supports_credentials=True)

app.logger.setLevel(logging.INFO)

# Required when using session.
# This is just a proof of concept, so the key is stored in the repository,
# BUT NEVER DO THAT IN REAL APPLICATIONS!
app.secret_key = "f3kfk934f0kk09fjv@#RFW"

# Hardcoded credentials for admin user.
USER = {"login": "admin", "password": "12345"}


# Decorator for a view function, checking if a user is logged in.
# Dummy implementation that checks the "logged_in" flag stored in
# the session.
def login_required(f):
    @wraps(f)
    def decorator_function(*args, **kwargs):
        if session.get("logged_in", False):
            return f(*args, **kwargs)
        app.logger.warning("Unauthorized access attempt!")
        return redirect(url_for("login"))

    return decorator_function


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")


# Page with exploit that sends malicious requests
# within the same domain.
@app.route("/exploit", methods=["GET"])
def exploit():
    return render_template("exploit.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login = request.form.get("login")
        password = request.form.get("password")

        if login == USER["login"] and password == USER["password"]:
            session["logged_in"] = True
            return redirect(url_for("home"))

        flash("Invalid credentials")

    return render_template("login.html")


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("home"))


# Example of a poorly designed API endpoint.
# Potentially dangerous method that changes the system's state is
# called via GET request.
@app.route("/sendout", methods=["GET"])
@login_required
def send_out_nudes_to_all_my_friends():
    message = "Your nudes have been sent!"
    app.logger.warning(message)
    flash(message)
    return redirect(url_for("home"))


@app.route("/password", methods=["POST"])
@login_required
def change_password():
    new_password = request.get_json()["new_password"]

    # For demonstration purposes only.
    # NEVER LOG SECRETES, ESPECIALLY IN PLAIN TEXT!
    app.logger.info(f"Password changed to {new_password}")
    flash("Your password has been changed!")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
