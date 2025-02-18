from flask import Flask, render_template, request, redirect, url_for, flash, session
from azure.storage.blob import BlobServiceClient
import uuid
import re
import requests
from dotenv import load_dotenv
from config import Config

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Azure Blob Storage Setup
BLOB_SERVICE_URL = f"https://{Config.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/"
blob_service_client = BlobServiceClient(account_url=BLOB_SERVICE_URL, credential=Config.AZURE_STORAGE_KEY)

# Removes invalid characters and replaces spaces with hyphens
def sanitize_filename(filename):
    filename = filename.lower().replace(" ", "-")  # Convert spaces to hyphens
    filename = re.sub(r"[^a-zA-Z0-9.\-_]", "", filename)  # Remove invalid characters
    return filename

# Render login form and handle authentication
@app.route("/", methods=["GET", "POST"])
def login():
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
                return redirect(url_for("user_products"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

# Admin dashboard
@app.route("/dashboard/admin")
def dashboard_admin():
    if not session.get("token"):
        return redirect(url_for("login"))
    return render_template("dashboard_admin.html", email=session["email"])

# User dashboard
@app.route("/dashboard/user")
def dashboard_user():
    if not session.get("token"):
        return redirect(url_for("login"))
    return render_template("dashboard_user.html", email=session["email"])

# Allow user to submit a product with an image uploaded to Azure Blob Storage
@app.route("/submit-product", methods=["GET", "POST"])
def submit_product():
    if not session.get("token"):
        return redirect(url_for("login"))

    if request.method == "POST":
        product_name = request.form["product_name"]
        product_description = request.form["product_description"]
        product_image = request.files["product_image"]

        if product_image:
            # Generate a unique and sanitized filename
            safe_filename = sanitize_filename(product_image.filename)
            unique_filename = f"{uuid.uuid4()}-{safe_filename}"  # Add UUID prefix

            # Define the full blob path (folder + filename)
            blob_path = f"{Config.AZURE_UPLOAD_FOLDER}/{unique_filename}"  # e.g., lightsproductimages_inquiries/uuid-filename.jpg
            print(blob_path)

            # Upload image to Azure Blob Storage
            try:
                blob_client = blob_service_client.get_blob_client(container=Config.AZURE_CONTAINER_NAME, blob=blob_path)
                blob_client.upload_blob(product_image, overwrite=True)

                # Generate public image URL
                image_url = f"https://{Config.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{Config.AZURE_CONTAINER_NAME}/{unique_filename}"

                # Send data to backend API
                response = requests.post(f"{Config.APIRS_SERVICE_API_URL}/submit-product",
                                         headers={"Authorization": f"Bearer {session['token']}"},
                                         json={
                                             "user_email": session["email"],
                                             "product_name": product_name,
                                             "product_description": product_description,
                                             "product_image_url": image_url
                                         })

                if response.status_code == 201:
                    flash("Product submitted successfully!", "success")
                    return redirect(url_for("user_products"))
                else:
                    flash("Error submitting product", "danger")

            except Exception as e:
                flash(f"Image upload failed: {str(e)}", "danger")

    return render_template("submit_product.html")

# Display products submitted by the user
@app.route("/user-products")
def user_products():
    if not session.get("token"):
        return redirect(url_for("login"))

    response = requests.get(f"{Config.BACKEND_URL}/get-user-products", headers={"Authorization": f"Bearer {session['token']}"})

    if response.status_code == 200:
        user_products = response.json()["products"]
    else:
        user_products = []

    return render_template("user_products.html", user_products=user_products)

# Display approved products
@app.route("/approved-products")
def approved_products():
    if not session.get("token"):
        return redirect(url_for("login"))

    response = requests.get(f"{Config.BACKEND_URL}/get-approved-products", headers={"Authorization": f"Bearer {session['token']}"})

    if response.status_code == 200:
        approved_products = response.json()["products"]
    else:
        approved_products = []

    return render_template("approved_products.html", approved_products=approved_products)

# Admin view of pending products
@app.route("/get-admin-pending-products", methods=["GET"])
def admin_pending_products():
    if not session.get("token") or session.get("role") != "admin":
        return redirect(url_for("login"))

    response = requests.get(f"{Config.BACKEND_URL}/get-admin-pending-products", headers={"Authorization": f"Bearer {session['token']}"})

    if response.status_code == 200:
        pending_products = response.json()["products"]
    else:
        pending_products = []

    return render_template("admin_pending_products.html", pending_products=pending_products)

# Admin view of approved products
@app.route("/get-admin-approved-products", methods=["GET"])
def admin_approved_products():
    if not session.get("token") or session.get("role") != "admin":
        return redirect(url_for("login"))

    response = requests.get(f"{Config.BACKEND_URL}/get-admin-approved-products", headers={"Authorization": f"Bearer {session['token']}"})

    if response.status_code == 200:
        approved_products = response.json()["products"]
    else:
        approved_products = []

    return render_template("admin_approved_products.html", approved_products=approved_products)
 
# Admin approves a product
@app.route("/admin-approve-product/<product_id>", methods=["GET", "POST"])
def admin_approve_product(product_id):
    if not session.get("token") or session.get("role") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        new_category = request.form["product_category"]
        
        response = requests.post(f"{Config.BACKEND_URL}/admin-approve-product", headers={"Authorization": f"Bearer {session['token']}"},
                                 json={"product_id": product_id, "product_category": new_category})

        if response.status_code == 200:
            flash("Product approved successfully!", "success")
            return redirect(url_for("admin_pending_products"))
        else:
            flash("Error approving product", "danger")

    # Fetch product details
    response = requests.get(f"{Config.BACKEND_URL}/admin-get-product/{product_id}", headers={"Authorization": f"Bearer {session['token']}"} )

    if response.status_code == 200:
        product = response.json()
    else:
        flash("Product not found", "danger")
        return redirect(url_for("admin_pending_products"))

    categories = [
        "Fluorescent tubes measuring less than or equal to 2 ft", 
        "Fluorescent tubes measuring greater than 2 ft and up to or equal to 4 ft", 
        "Fluorescent tubes measuring greater than 4 ft", 
        "Compact Fluorescent Lights (CFL) / Screw-In Induction Lamps", 
        "Light Emitting Diodes (LED) - Bulbs",
        "Light Emitting Diodes (LED) - Tubes and Other", 
        "High Intensity Discharge (HID), Germicidal, Special Purpose and Other", 
        "Incandescent / Halogen", 
        "Miniature Bulb Package",
        "Designated Small Fixtures / Decorative Light Strings", 
        "Fixture Category A - Portable Fixtures with a plug, cord, or battery", 
        "Fixture Category A - Emergency / Egress Lights", 
        "Fixture Category A - Small Outdoor Fixtures",
        "Fixture Category A - Decorative Fixtures", 
        "Fixture Category A - Chandeliers and Ceiling Fans", 
        "Fixture Category A - Linear Fixtures (including linear shop lights and linear pool / fountain fixtures)", 
        "Fixture Category B - Non-Linear Fixtures (commercial and industrial)", 
        "Large Outdoor Fixtures Designed for use in institutional, commercial, and industrial settings", 
        "Lighting Ballasts / Transformers (not integrated into lamps or fixtures)"
        ]

    return render_template("admin_approve_product.html", product=product, categories=categories)

# Logout user
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)