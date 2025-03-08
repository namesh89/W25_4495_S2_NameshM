from flask import Flask, request, jsonify
from azure.data.tables import TableServiceClient
from sentence_transformers import SentenceTransformer, util
import numpy as np
from config import Config
from azure.core.credentials import AzureNamedKeyCredential


app = Flask(__name__)
app.config.from_object(Config)

# Create credential object
credential = AzureNamedKeyCredential(Config.AZURE_STORAGE_ACCOUNT_NAME, Config.AZURE_STORAGE_ACCOUNT_KEY)

# Azure Storage URLs
BLOB_SERVICE_URL = f"https://{Config.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/"
TABLE_SERVICE_URL = f"https://{Config.AZURE_STORAGE_ACCOUNT_NAME}.table.core.windows.net/"

# Load NLP model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Method to fetch product data from Azure Table Storage
def fetch_products_from_azure():
    try:
        service = TableServiceClient(endpoint=TABLE_SERVICE_URL, credential=credential)
        table_client = service.get_table_client(table_name=Config.AZURE_TABLE_NAME)

        products = []
        entities = table_client.list_entities()

        for entity in entities:
            products.append({
                "product_category": entity["PartitionKey"],
                "product_id": entity.get("product_id", ""),
                "product_description": entity.get("product_description", ""),
                "row_key": entity["RowKey"]
            })
        
        return products

    except Exception as e:
        print(f"Error fetching products from Azure Table Storage: {e}")
        return []

# Method to compute similarity using NLP
def find_best_match(new_product_name, new_product_description, products):
    product_texts = [f"{p['product_category']} {p['product_description']}" for p in products]
    new_product_text = f"{new_product_name} {new_product_description}"

    # Encode using Sentence-BERT
    embeddings = model.encode([new_product_text] + product_texts, convert_to_tensor=True)
    
    # Compute cosine similarity
    similarities = util.pytorch_cos_sim(embeddings[0], embeddings[1:]).squeeze(0)

    # Get best match
    best_idx = np.argmax(similarities).item()
    best_match = products[best_idx]
    similarity_score = similarities[best_idx].item()

    return best_match, similarity_score * 100  # Convert to percentage

@app.route("/predict-category", methods=["POST"])
def predict_category():
    try:
        data = request.get_json()
        product_name = data.get("product_name")
        product_description = data.get("product_description")
        product_image_url = data.get("product_image_url")

        if not all([product_name, product_description, product_image_url]):
            return jsonify({"error": "Missing required fields"}), 400

        # Fetch existing products
        existing_products = fetch_products_from_azure()

        if not existing_products:
            return jsonify({"error": "No products found in database"}), 500

        # Find best match
        best_match, accuracy = find_best_match(product_name, product_description, existing_products)

        print(best_match)
        print(accuracy)

        # Return predicted product_category
        return jsonify({"product_category": best_match["product_category"]}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)