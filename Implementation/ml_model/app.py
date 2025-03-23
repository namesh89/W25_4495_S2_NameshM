from flask import Flask, request, jsonify
from azure.data.tables import TableServiceClient
from sentence_transformers import SentenceTransformer, util
import numpy as np
from config import Config
from azure.core.credentials import AzureNamedKeyCredential

import requests
from PIL import Image
from io import BytesIO
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
from sklearn.metrics.pairwise import cosine_similarity
from tensorflow.keras.models import Model

#import os
#os.environ["TRANSFORMERS_NO_TF"] = "1"

app = Flask(__name__)
app.config.from_object(Config)

# Create credential object
credential = AzureNamedKeyCredential(Config.AZURE_STORAGE_ACCOUNT_NAME, Config.AZURE_STORAGE_ACCOUNT_KEY)

# Azure Storage URLs
BLOB_SERVICE_URL = f"https://{Config.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/"
TABLE_SERVICE_URL = f"https://{Config.AZURE_STORAGE_ACCOUNT_NAME}.table.core.windows.net/"

# Load SBERT models
model_pc = SentenceTransformer('all-mpnet-base-v2')
model_pd = SentenceTransformer('bert-large-nli-stsb-mean-tokens')

# Load ResNet50 model (without top layer, for feature extraction)
model_img = ResNet50(weights='imagenet', include_top=False, pooling='avg')


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
                "row_key": entity["RowKey"],
                "image_url": entity["image_url"]
            })
        
        return products

    except Exception as e:
        print(f"Error fetching products from Azure Table Storage: {e}")
        return []


# Method to compute similarity using NLP
def find_best_match(new_product_name, new_product_description, new_product_image_url, products):

    best_overall_match = None
    best_overall_score = 0

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


def find_best_match_image(new_product_image_url, products):

    best_score = 0
    best_match = None

    # Preprocess new image
    try:
        response = requests.get(new_product_image_url, timeout=10)
        img = Image.open(BytesIO(response.content)).convert('RGB')
        img = img.resize((224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        new_features = model_img.predict(img_array)
    except Exception as e:
        print(f"Error processing new product image: {e}")
        return None, 0

    for product in products:
        try:
            response = requests.get(product['image_url'], timeout=10)
            img = Image.open(BytesIO(response.content)).convert('RGB')
            img = img.resize((224, 224))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)
            existing_features = model_img.predict(img_array)

            similarity = cosine_similarity(new_features, existing_features)[0][0]

            if similarity > best_score:
                best_score = similarity
                best_match = product

        except Exception as e:
            print(f"Error processing existing product image ({product.get('image_url')}): {e}")
            continue

    return best_match, best_score * 100  # Convert to percentage


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
        #best_match, accuracy = find_best_match(product_name, product_description, product_image_url, existing_products)
        best_match, accuracy = find_best_match_image(product_image_url, existing_products)

        print()
        print(best_match)
        print(accuracy)
        print()

        # Return predicted product_category
        return jsonify({"product_category": best_match["product_category"]}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5002)