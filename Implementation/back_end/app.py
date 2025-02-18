from flask import Flask, request, jsonify
from azure.data.tables import TableServiceClient, TableEntity
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from werkzeug.security import check_password_hash
import uuid

from config import Config
from utils import verify_password

app = Flask(__name__)
app.config.from_object(Config)  # Load configuration from config.py

jwt = JWTManager(app)

# Azure Table Storage connection
table_service = TableServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
user_table = table_service.get_table_client(Config.AZURE_USER_TABLE_NAME)
product_table = table_service.get_table_client(Config.AZURE_TEMP_PRODUCT_TABLE_NAME)

# Handle user login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Query user by email
    try:
        query = f"Email eq '{email}'"
        users = list(user_table.query_entities(query))

        if not users:
            return jsonify({"error": "Invalid email or password"}), 401

        user = users[0]  # First matching user
        stored_password = user["PasswordHash"]

        # Verify password
        if not verify_password(stored_password, password):
            return jsonify({"error": "Invalid email or password"}), 401

        # Determine user role
        role = "admin" if email.lower() == "admin@test.com" else "user"

        # Generate JWT token
        access_token = create_access_token(identity=user["RowKey"])
        return jsonify({
            "message": "Login successful", 
            "token": access_token,
            "email": email,
            "role": role
        }), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Save user-submitted product info to Azure Table Storage
@app.route("/submit-product", methods=["POST"])
@jwt_required()
def submit_product():
    try:
        data = request.get_json()
        user_email = get_jwt_identity()  # Get user email from JWT
        product_name = data.get("product_name")
        product_description = data.get("product_description")
        product_image_url = data.get("product_image_url")

        if not all([product_name, product_description, product_image_url]):
            return jsonify({"error": "Missing required fields"}), 400

        product_id = str(uuid.uuid4())

        # Save to Azure Table Storage
        product_entity = TableEntity()
        product_entity["PartitionKey"] = user_email
        product_entity["RowKey"] = product_id
        product_entity["ProductName"] = product_name
        product_entity["ProductDescription"] = product_description
        product_entity["ProductImageUrl"] = product_image_url
        product_entity["ProductCategory"] = ""
        product_entity["Status"] = "Pending"

        product_table.create_entity(product_entity)

        return jsonify({"message": "Product submitted successfully!", "product_id": product_id}), 201

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# List pending products for the logged-in user
@app.route("/get-user-products", methods=["GET"])
@jwt_required()
def get_user_products():
    user_email = get_jwt_identity()

    # Query Azure Table Storage for user's pending products
    query = f"PartitionKey eq '{user_email}' and Status eq 'Pending'"
    products = list(product_table.query_entities(query))

    product_list = [{
        "product_id": product["RowKey"],
        "product_name": product["ProductName"],
        "product_description": product["ProductDescription"],
        "product_image_url": product["ProductImageUrl"],
        "product_category": product["ProductCategory"],
        "status": product["Status"]
    } for product in products]

    return jsonify({"products": product_list}), 200

# List approved products for the logged-in user
@app.route("/get-approved-products", methods=["GET"])
@jwt_required()
def get_approved_products():
    user_email = get_jwt_identity()

    # Query Azure Table Storage for user's approved products
    query = f"PartitionKey eq '{user_email}' and Status eq 'Approved'"
    products = list(product_table.query_entities(query))

    product_list = [{
        "product_id": product["RowKey"],
        "product_name": product["ProductName"],
        "product_description": product["ProductDescription"],
        "product_image_url": product["ProductImageUrl"],
        "product_category": product["ProductCategory"],
        "status": product["Status"]
    } for product in products]

    return jsonify({"products": product_list}), 200

# Admin: List all pending products
@app.route("/get-admin-pending-products", methods=["GET"])
@jwt_required()
def admin_get_pending_products():
    admin_email = get_jwt_identity()
    if not admin_email:
        return jsonify({"error": "Unauthorized"}), 403

    query = "Status eq 'Pending'"
    products = list(product_table.query_entities(query))

    product_list = [{
        "product_id": product["RowKey"],
        "user_email": product["PartitionKey"],
        "product_name": product["ProductName"],
        "product_description": product["ProductDescription"],
        "product_image_url": product["ProductImageUrl"],
        "product_category": product["ProductCategory"],
        "status": product["Status"]
    } for product in products]

    return jsonify({"products": product_list}), 200

# Admin: List all approved products
@app.route("/get-admin-approved-products", methods=["GET"])
@jwt_required()
def admin_get_approved_products():
    admin_email = get_jwt_identity()
    if not admin_email:
        return jsonify({"error": "Unauthorized"}), 403

    query = "Status eq 'Approved'"
    products = list(product_table.query_entities(query))

    product_list = [{
        "product_id": product["RowKey"],
        "user_email": product["PartitionKey"],
        "product_name": product["ProductName"],
        "product_description": product["ProductDescription"],
        "product_image_url": product["ProductImageUrl"],
        "product_category": product["ProductCategory"],
        "status": product["Status"]
    } for product in products]

    return jsonify({"products": product_list}), 200

# Admin: Approve or override a product category
@app.route("/admin-approve-product", methods=["POST"])
@jwt_required()
def approve_product():
    admin_email = get_jwt_identity()
    if not admin_email:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    product_id = data.get("product_id")
    new_category = data.get("product_category")

    if not product_id or not new_category:
        return jsonify({"error": "Product ID and category are required"}), 400

    # Fetch the product entity
    try:
        query = f"RowKey eq '{product_id}'"
        products = list(product_table.query_entities(query))
        
        if not products:
            return jsonify({"error": "Product not found"}), 404

        product = products[0]  # There should be only one match

        # Update the product category and status
        product["ProductCategory"] = new_category
        product["Status"] = "Approved"

        product_table.update_entity(product, mode="merge")

        return jsonify({"message": "Product approved successfully!"}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Admin: Fetch details of a specific product
@app.route("/admin-get-product/<product_id>", methods=["GET"])
@jwt_required()
def admin_get_product(product_id):
    admin_email = get_jwt_identity()
    if not admin_email:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        # Query to find the product
        query = f"RowKey eq '{product_id}'"
        products = list(product_table.query_entities(query))

        if not products:
            return jsonify({"error": "Product not found"}), 404

        product = products[0]  # There should be only one match

        product_data = {
            "product_id": product["RowKey"],
            "user_email": product["PartitionKey"],
            "product_name": product["ProductName"],
            "product_description": product["ProductDescription"],
            "product_image_url": product["ProductImageUrl"],
            "product_category": product["ProductCategory"],
            "status": product["Status"]
        }

        return jsonify(product_data), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)