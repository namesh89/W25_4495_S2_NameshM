from flask import Flask, request, jsonify
from azure.data.tables import TableServiceClient
from sentence_transformers import SentenceTransformer
import numpy as np
from config import Config
from azure.core.credentials import AzureNamedKeyCredential

import requests
from PIL import Image
from io import BytesIO
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Model
import base64

app = Flask(__name__)
app.config.from_object(Config)

# Create credential object
credential = AzureNamedKeyCredential(Config.AZURE_STORAGE_ACCOUNT_NAME, Config.AZURE_STORAGE_ACCOUNT_KEY)

# Azure Storage URL
TABLE_SERVICE_URL = f"https://{Config.AZURE_STORAGE_ACCOUNT_NAME}.table.core.windows.net/"

# Load models
model_pc = SentenceTransformer('all-mpnet-base-v2')
model_pd = SentenceTransformer('bert-large-nli-stsb-mean-tokens')
model_img = ResNet50(weights='imagenet', include_top=False, pooling='avg')


def decode_array(encoded_string):
    decoded = base64.b64decode(encoded_string)
    return np.frombuffer(decoded, dtype=np.float32)


def fetch_products_with_embeddings():
    try:
        service = TableServiceClient(endpoint=TABLE_SERVICE_URL, credential=credential)
        table_client = service.get_table_client(table_name=Config.AZURE_TABLE_NAME)

        products = []
        for entity in table_client.list_entities():
            products.append({
                "product_category": entity["PartitionKey"],
                "product_id": entity.get("product_id", ""),
                "product_description": entity.get("product_description", ""),
                "row_key": entity["RowKey"],
                "image_url": entity.get("image_url", ""),
                "embedding_pc": decode_array(entity.get("text_embedding_pc", "")),
                "embedding_pd": decode_array(entity.get("text_embedding_pd", "")),
                "embedding_img": decode_array(entity.get("image_embedding", ""))
            })
        return products
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []


def cosine_sim(v1, v2):
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


def find_best_match_pc(new_product_name, products):
    new_pc_embedding = model_pc.encode(new_product_name)

    best_match = None
    best_score = 0

    for p in products:
        score_pc = cosine_sim(new_pc_embedding, p['embedding_pc'])

        if score_pc > best_score:
            best_score = score_pc
            best_match = p

    return best_match, best_score * 100


def find_best_match_pd(new_product_description, products):
    new_pd_embedding = model_pd.encode(new_product_description)

    best_match = None
    best_score = 0

    for p in products:
        score_pd = cosine_sim(new_pd_embedding, p['embedding_pd'])

        if score_pd > best_score:
            best_score = score_pd
            best_match = p

    return best_match, best_score * 100


def find_best_match_image(new_product_image_url, products):
    try:
        response = requests.get(new_product_image_url, timeout=10)
        img = Image.open(BytesIO(response.content)).convert('RGB')
        img = img.resize((224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        new_img_embedding = model_img.predict(img_array)[0]
    except Exception as e:
        print(f"Error processing image: {e}")
        return None, 0

    best_match = None
    best_score = 0

    for p in products:
        score = cosine_sim(new_img_embedding, p['embedding_img'])
        if score > best_score:
            best_score = score
            best_match = p

    return best_match, best_score * 100


@app.route("/predict-category", methods=["POST"])
def predict_category():
    try:
        data = request.get_json()
        name = data.get("product_name")
        desc = data.get("product_description")
        image_url = data.get("product_image_url")

        if not all([name, desc, image_url]):
            return jsonify({"error": "Missing required fields"}), 400

        products = fetch_products_with_embeddings()
        if not products:
            return jsonify({"error": "No products found in database"}), 500

        text_match_pc, text_score_pc = find_best_match_pc(name, products)
        text_match_pd, text_score_pd = find_best_match_pd(desc, products)
        image_match, image_score = find_best_match_image(image_url, products)

        # Create a list of matches and scores
        matches = [
            (text_match_pc, text_score_pc),
            (text_match_pd, text_score_pd),
            (image_match, image_score)
        ]

        # Find the match with the highest score
        final_match, final_score = max(matches, key=lambda x: x[1])
        
        filtered_final_match = {key: value for key, value in final_match.items()
                    if key not in ["image_url", "embedding_pc", "embedding_pd", "embedding_img"]}
        
        print("\nFinal Match:")
        for key, value in filtered_final_match.items():
            print(f"{key}: {value}")

        print(f"\nFinal Score: {final_score}\n")

        return jsonify({
            "product_category": final_match["product_category"],
            "match_score": round(final_score, 2)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5002)