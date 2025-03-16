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
    'bert-base-nli-mean-tokens',
    'bert-large-nli-stsb-mean-tokens',
    'distilbert-base-nli-stsb-mean-tokens',
    'roberta-base-nli-stsb-mean-tokens',
    'roberta-large-nli-stsb-mean-tokens',
    'paraphrase-multilingual-MiniLM-L12-v2',
    'distiluse-base-multilingual-cased-v2'
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
    "T8 18-inch Fluorescent Tube Light",
    "T5 3-ft Fluorescent Tube for Office Lighting",
    "T12 5-ft Fluorescent Tube for Warehouse Use",
    "Philips 13W Spiral CFL Bulb",
    "GE 10W LED A19 Bulb",
    "T8 4-ft LED Tube Light for Commercial Use",
    "Metal Halide 400W HID Lamp for Stadium Lighting",
    "GE 43W Halogen A19 Bulb",
    "12V LED Miniature Bulb for Automotive Dashboard",
    "LED Warm White String Lights for Holiday Decoration",
    "Rechargeable LED Work Light with Handle",
    "Lithonia LED Exit Sign with Battery Backup",
    "Solar-Powered LED Wall Lantern for Outdoor Use",
    "Crystal Chandelier Pendant Light for Dining Room",
    "Hunter 52-inch Ceiling Fan with LED Light Kit",
    "4-ft LED Shop Light for Garages",
    "High Bay LED Light for Warehouse Applications",
    "Streetlight LED Fixture for Highway Lighting",
    "Advance T8 Electronic Ballast for Fluorescent Tubes"
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
    model_name, top_k_acc, mrr = evaluate_model(model, k=5)
    results.append([model_name, top_k_acc, mrr])

# Convert results to DataFrame and display
df_results = pd.DataFrame(results, columns=["Model Name", "Top-K Accuracy", "Mean Reciprocal Rank (MRR)"])
print(df_results)

# File path
file_path = "C:/Users/names/OneDrive - Douglas College/Semester 7/Applied Research Project - CSIS4495 002/2. Progress Reports/Progress Report 2/model_evaluation_pc.csv"

# Export DataFrame to CSV
df_results.to_csv(file_path, index=True, mode='w')
print("CSV file has been successfully replaced.")