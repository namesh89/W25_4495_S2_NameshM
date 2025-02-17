from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
from dotenv import load_dotenv
from config import Config

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

@app.route("/", methods=["GET", "POST"])
def login():
    """Render login form and handle authentication."""
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Send request to backend API
        response = requests.post(f"{Config.BACKEND_URL}/login", json={"email": email, "password": password})

        if response.status_code == 200:
            data = response.json()
            session["token"] = data["token"]
            session["email"] = data["email"]
            session["role"] = data["role"]

            # Redirect based on role
            if data["role"] == "admin":
                return redirect(url_for("dashboard_admin"))
            else:
                return redirect(url_for("dashboard_user"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

@app.route("/dashboard/admin")
def dashboard_admin():
    """Admin dashboard."""
    if not session.get("token"):
        return redirect(url_for("login"))
    return render_template("dashboard_admin.html", email=session["email"])

@app.route("/dashboard/user")
def dashboard_user():
    """User dashboard."""
    if not session.get("token"):
        return redirect(url_for("login"))
    return render_template("dashboard_user.html", email=session["email"])

@app.route("/logout")
def logout():
    """Logout user."""
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)