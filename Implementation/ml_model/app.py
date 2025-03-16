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

    # Hugging Face models
    model_name_pc = 'all-mpnet-base-v2'
    model_name_pd = 'bert-large-nli-stsb-mean-tokens'

    # Load NLP models
    model_pc = SentenceTransformer(model_name_pc)
    model_pd = SentenceTransformer(model_name_pd)

    product_texts_pc = [p['product_category'] for p in products]
    new_product_text_pc = new_product_name
    product_texts_pd = [p['product_description'] for p in products]
    new_product_text_pd = new_product_description

    # Encode using Sentence-BERT
    embeddings_pc = model_pc.encode([new_product_text_pc] + product_texts_pc, convert_to_tensor=True)
    embeddings_pd = model_pd.encode([new_product_text_pd] + product_texts_pd, convert_to_tensor=True)
        
    # Compute cosine similarity
    similarities_pc = util.pytorch_cos_sim(embeddings_pc[0], embeddings_pc[1:]).squeeze(0)
    similarities_pd = util.pytorch_cos_sim(embeddings_pd[0], embeddings_pd[1:]).squeeze(0)

    # Get best match
    best_id_pc = np.argmax(similarities_pc).item()
    best_match_pc = products[best_id_pc]
    similarity_score_pc = similarities_pc[best_id_pc].item()

    best_id_pd = np.argmax(similarities_pd).item()
    best_match_pd = products[best_id_pd]
    similarity_score_pd = similarities_pd[best_id_pd].item()

    # Determine the best match overall
    if similarity_score_pc > best_overall_score:
        best_overall_score = similarity_score_pc
        best_overall_match = best_match_pc
        
    if similarity_score_pd > best_overall_score:
        best_overall_score = similarity_score_pd
        best_overall_match = best_match_pd

    print("Best Match (based on Category):", best_match_pc)
    print("Similarity Score (based on Category):", similarity_score_pc * 100)
    print("Best Match (based on Description):", best_match_pd)
    print("Similarity Score (based on Description):", similarity_score_pd * 100)
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