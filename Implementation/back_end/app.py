from flask import Flask, request, jsonify
from azure.data.tables import TableServiceClient
from flask_jwt_extended import JWTManager, create_access_token

from config import Config
from utils import verify_password

app = Flask(__name__)
app.config.from_object(Config)  # Load configuration from config.py

jwt = JWTManager(app)

# Azure Table Storage connection
table_service = TableServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
user_table = table_service.get_table_client(Config.AZURE_USER_TABLE_NAME)
product_table = table_service.get_table_client(Config.AZURE_TEMP_PRODUCT_TABLE_NAME)

@app.route("/login", methods=["POST"])
def login():
    """Handle user login."""
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

if __name__ == "__main__":
    app.run(debug=True)