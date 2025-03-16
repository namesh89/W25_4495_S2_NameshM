import os
import numpy as np
import torch
import pandas as pd
from sentence_transformers import SentenceTransformer, util

# Define the transformer models to evaluate
models = [
    'all-MiniLM-L6-v2',
    'all-MiniLM-L12-v2',
    'all-mpnet-base-v2',
    'distilbert-base-nli-stsb-mean-tokens',
    'bert-base-nli-mean-tokens',
    'roberta-base-nli-stsb-mean-tokens',
    'paraphrase-multilingual-MiniLM-L12-v2'
]

# Existing product categories
existing_product_category = [
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

# New product names
new_product_name = [
    "Philips 18-inch T8 Fluorescent Tube 15W",
    "GE 36-inch T8 Fluorescent Tube 30W",
    "Sylvania 60-inch T12 Fluorescent Tube 40W",
    "Osram 13W Spiral CFL Bulb",
    "Cree 10W A19 LED Bulb",
    "Philips 4-ft LED Tube Light 18W",
    "GE 250W Metal Halide HID Lamp",
    "Sylvania 72W Halogen Soft White Bulb",
    "Philips 5W Miniature E10 Indicator Bulb",
    "Holiday Bright LED Decorative String Lights 20ft",
    "Black+Decker Rechargeable LED Work Light",
    "Lithonia LED Exit Sign Emergency Light Combo",
    "Hampton Bay 12-inch Outdoor Wall Lantern",
    "Kichler Crystal Mini Pendant Light",
    "Hunter 52-inch LED Ceiling Fan with Light",
    "Lithonia 48-inch LED Linear Shop Light",
    "GE High Bay LED Fixture 200W",
    "Philips 300W LED Parking Lot Light",
    "Advance ICN-2S40-N T8 Electronic Ballast"
]

# Ground truth mapping (expected indices of correct matches)
true_indices = list(range(len(new_product_name)))

# Function to evaluate a model using Top-K Accuracy and MRR
def evaluate_model(model_name, k=5):
    print(f"Evaluating Model: {model_name} with k={k}")
    
    # Load the model
    model = SentenceTransformer(model_name)
    
    # Encode existing product categories
    category_embeddings = model.encode(existing_product_category, convert_to_tensor=True)
    
    top_k_correct = 0
    mrr_total = 0
    total_queries = len(new_product_name)
    
    # Iterate through each new product
    for i, query in enumerate(new_product_name):
        query_embedding = model.encode(query, convert_to_tensor=True)
        
        # Compute cosine similarity
        similarity_scores = util.pytorch_cos_sim(query_embedding, category_embeddings)[0]
        
        # Get the Top-K highest scoring indices
        top_k_indices = torch.topk(similarity_scores, k).indices.tolist()
        
        # Check if the correct match is in the Top-K results
        if true_indices[i] in top_k_indices:
            top_k_correct += 1
        
        # Compute rank of the correct match
        sorted_indices = torch.argsort(similarity_scores, descending=True).tolist()
        rank = sorted_indices.index(true_indices[i]) + 1  # Rank is 1-based
        mrr_total += 1 / rank
    
    # Compute final scores
    top_k_accuracy = top_k_correct / total_queries
    mrr_score = mrr_total / total_queries
    
    return model_name, top_k_accuracy, mrr_score

# Evaluate all models and store results
results = []
for model in models:
    model_name, top_k_acc, mrr = evaluate_model(model, k=1)
    results.append([model_name, top_k_acc, mrr])

# Convert results to DataFrame and display
df_results = pd.DataFrame(results, columns=["Model Name", "Top-K Accuracy", "Mean Reciprocal Rank (MRR)"])
print(df_results)

# File path
file_path = "C:/Users/names/OneDrive - Douglas College/Semester 7/Applied Research Project - CSIS4495 002/2. Progress Reports/Progress Report 2/model_evaluation_pc.csv"

# Export DataFrame to CSV
df_results.to_csv(file_path, index=True, mode='w')
print("CSV file has been successfully replaced.")