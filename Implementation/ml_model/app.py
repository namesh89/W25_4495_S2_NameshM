from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/predict-category", methods=["POST"])
def predict_category():
    try:
        data = request.get_json()
        product_name = data.get("product_name")
        product_description = data.get("product_description")
        product_image_url = data.get("product_image_url")

        if not all([product_name, product_description, product_image_url]):
            return jsonify({"error": "Missing required fields"}), 400

        # Placeholder ML logic - Replace with actual model
        predicted_category = "TEST"

        return jsonify({"product_category": predicted_category}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)