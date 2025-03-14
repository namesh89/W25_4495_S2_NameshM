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

# List of models to run simultaneously
model_names = [
    'all-MiniLM-L6-v2',
    'all-MiniLM-L12-v2',
    'all-mpnet-base-v2',
    'distilbert-base-nli-stsb-mean-tokens',
    'bert-base-nli-mean-tokens',
    'roberta-base-nli-stsb-mean-tokens',
    'paraphrase-multilingual-MiniLM-L12-v2'
]

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

    best_overall_match = None
    best_overall_score = 0

    for model_name in model_names:

        # Load NLP model
        model = SentenceTransformer(model_name)

        product_texts1 = [p['product_category'] for p in products]
        new_product_text1 = new_product_name
        product_texts2 = [p['product_description'] for p in products]
        new_product_text2 = new_product_description

        # Encode using Sentence-BERT
        embeddings1 = model.encode([new_product_text1] + product_texts1, convert_to_tensor=True)
        embeddings2 = model.encode([new_product_text2] + product_texts2, convert_to_tensor=True)
        
        # Compute cosine similarity
        similarities1 = util.pytorch_cos_sim(embeddings1[0], embeddings1[1:]).squeeze(0)
        similarities2 = util.pytorch_cos_sim(embeddings2[0], embeddings2[1:]).squeeze(0)

        # Get best match
        best_idx1 = np.argmax(similarities1).item()
        best_match1 = products[best_idx1]
        similarity_score1 = similarities1[best_idx1].item()

        best_idx2 = np.argmax(similarities2).item()
        best_match2 = products[best_idx2]
        similarity_score2 = similarities2[best_idx2].item()

        # Determine the best match overall
        if similarity_score1 > best_overall_score:
            best_overall_score = similarity_score1
            best_overall_match = best_match1
        
        if similarity_score2 > best_overall_score:
            best_overall_score = similarity_score2
            best_overall_match = best_match2

        print(f"Model: ", model_name)
        print("Best Match (Category):", best_match1['product_category'])
        print("Similarity Score (Category):", similarity_score1 * 100)
        print("Best Match (Description):", best_match2['product_description'])
        print("Similarity Score (Description):", similarity_score2 * 100)
        print()

    return best_overall_match, best_overall_score * 100  # Convert to percentage

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

        # Return predicted product_category
        return jsonify({"product_category": best_match["product_category"]}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)