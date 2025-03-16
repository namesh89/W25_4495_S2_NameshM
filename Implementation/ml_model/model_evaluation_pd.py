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

# Existing product descriptions
existing_product_description = [
    "Includes all diameters and light outputs, shaped fluorescent tubes, and UV-A and UV-B tubes.",
    "Fluorescent bulbs that are typically similar in size and intended to replace an incandescent (traditional) light bulb, including pin-type sockets, covered CFLs and various output wattages. Includes screw-in induction lamps.",
    "Solid-state bulbs that are typically similar in size and intended to replace CFLs or traditional incandescent / halogen light bulbs, including pin-type or screw-in bulbs of various output wattages.",
    "Solid-state tubes of all lengths and shapes for all lighting applications, and other lamps / bulbs used for specialty purposes or industrial lighting applications (e.g. LED HID replacement lighting).",
    "Includes all HID technologies that contain mercury, such as High-Pressure Sodium (HPS), Low-Pressure Sodium (LPS), Mercury Vapor and Metal Halide, as well as UV-C / Germicidal lamps and tubes, Tubular Induction lamps (circular, square, U etc.), UHP replacement lamps (projector etc.), Neon replacement lamps, etc.",
    "Filament lamps of all shapes, sizes and wattages.",
    "Miniature bulbs are small, or very small bulbs. They can be LED, incandescent, halogen or neon and are typically designed and sold as replacement bulbs for applications such as: portable lighting (i.e., handheld flashlights), indicating, signaling, signage, emergency, electronic displays, automotive and transportation and decorative light strings / tape / ribbon / rope.",
    "Book Lights (including Kindle Lights).",
    "Snake Lights.",
    "Bike Lights.",
    "Flashlights, Camping Headlamps, and Handheld Spotlights.",
    "Clamp Spotlights and Clip Lamps.",
    "Lamp-holders (stand-alone and single lamp only).",
    "Lanterns and Electric Candles.",
    "Night Lights.",
    "Single Remote Head for Track / Egress Lighting (including replacement heads).",
    "Utility / Closet Lights (portable and battery powered only).",
    "Floating / Submersible Lights for pools, ponds, bathtubs, etc. (portable and battery powered only).",
    "Puck / Disk Lights - Compact lighting fixture used for cabinets or display lighting that contains the housing and lamp in a circular (round or oval) 'puck' or 'disk'. May be surface mounted or recessed. Limited to those under 4 inches in diameter and 2 inches in depth.",
    "Path / Walkway / Garden / In-Grade / Border / Step Lights (solar powered only).",
    "Christmas Light Strings and Light Strings - Products are reported and applied fees in increments of 100 lights. Products of 100 lights or less are applied for one recycling fee. Products with greater than 100 lights are charged one recycling fee per 100 light increments. For example, a light string of 460 lights would be reported as 5 units and assessed five fees.",
    "Rope / Strip / Ribbon / Tape Lights - Products are reported and applied fees in increments of 10 meters. Products of 10 meters or less are applied one recycling fee. Products greater than 10 meters are charged one recycling fee per 10-meter increment (i.e., 38 meters of rope lights would be reported as 4 units and assessed four fees). Members may choose to calculate a fee rate / unit sold to apply at point of sale and then bundle this into increments of 10 meters / $0.15 for reporting purposes.",
    "Stake Lights (set of connected units).",
    "Desk Lamps.",
    "Table Lamps.",
    "Floor Lamps.",
    "Portable Flood Lights.",
    "Work Lights (including work string lights).",
    "Emergency / Egress Lights.",
    "Bollard.",
    "Post Lighting (consumer applications only).",
    "Path / Walkway / Garden / In-Grade / Border / Step Lights (non-solar powered only).",
    "Porch / Patio Lights.",
    "Security Lighting (with or without integrated cameras) - Including residential-type security floodlights.",
    "Pool and Fountain Fixtures.",
    "Wall Mount / Small Flood - including commercial 'wall packs' and flood lights less than 250 W.",
    "Flush / Semi-Flush.",
    "Lamp-holders (stand-alone and for more than one lamp).",
    "Pendant.",
    "Recessed / Pot - Fee is only applied to the housing if housing and trims are sold separately.",
    "Fixed Track and Canopy.",
    "Under Cabinet (including linear fluorescent types).",
    "Wall Mount (including sconces).",
    "Chandeliers.",
    "Ceiling Fans with Lights.",
    "Strip Lights.",
    "Surfaced, Suspended, and Wall Mount Linear Fixtures.",
    "Troffers (recessed and non-recessed).",
    "LED Panel Lighting (surfaced and suspended).",
    "High / Low Bay Lighting.",
    "Parking Garage Fixtures (Ceiling and Wall Mount).",
    "Stage Lighting.",
    "Area, Highway, Street, Post Lighting. Pole or arm mounted luminaries for sidewalk, street, highway, pathway or post-top lighting, including 'shoeboxes' and 'cobra heads'. Non-consumer applications only.",
    "Flood Lights and Sports Lights - (≥250 W) designed for use in sports fields, stadiums, arenas, tracks, courts, industrial yards, parking lots etc.",
    "Ballasts, all types (i.e., compact fluorescent, electronic, HID, magnetic etc.)."
]

# New product descriptions
new_product_description = [
    "All sizes and brightness levels of shaped fluorescent tubes, including UV-A and UV-B varieties.",
    "Compact fluorescent bulbs designed to replace traditional incandescent ones, including pin-type sockets, CFLs, and screw-in induction lamps.",
    "LED bulbs designed to replace CFLs, incandescent, or halogen lights, available in different wattages with pin-type or screw-in bases.",
    "LED tubes of various sizes and shapes for general and industrial lighting, including specialty lamps like HID replacements.",
    "All mercury-containing HID lamps, including HPS, LPS, Mercury Vapor, Metal Halide, UV-C lamps, induction, UHP, and neon replacements.",
    "Traditional filament lamps in different shapes, sizes, and wattage levels.",
    "Small LED, incandescent, halogen, or neon bulbs used for flashlights, signs, emergencies, vehicle lighting, and decorative applications.",
    "Portable book lights, including those designed for Kindle e-readers.",
    "Flexible snake-style lights for various lighting needs.",
    "Lights designed specifically for bicycles to enhance visibility.",
    "Includes handheld flashlights, camping headlamps, and portable spotlights for outdoor use.",
    "Spotlights and lamps with clamps or clips for easy attachment.",
    "Individual lamp holders designed to hold and power a single light.",
    "Battery-powered lanterns and electric candles for ambient lighting.",
    "Small lights designed to provide soft illumination at night.",
    "Individual remote lighting heads for track or emergency exit lighting, including replacements.",
    "Battery-powered utility and closet lights for compact spaces.",
    "Waterproof floating lights for pools, bathtubs, or ponds, powered by batteries.",
    "Compact, round puck or disk-shaped lights for cabinets and displays, either recessed or surface-mounted, under 4 inches wide and 2 inches deep.",
    "Solar-powered lights designed for pathways, gardens, steps, and outdoor borders.",
    "Christmas and decorative light strings are charged recycling fees based on every 100 lights, with a string of 460 lights counted as five units.",
    "Flexible rope, strip, ribbon, and tape lights are charged fees per 10-meter segment, with 38 meters counted as four units for recycling.",
    "A set of outdoor lights connected together, typically placed along pathways or gardens for illumination.",
    "Small portable lamps designed for desks or workspaces, providing focused lighting for reading or tasks.",
    "Compact lamps placed on tables or nightstands, used for decorative or functional indoor lighting.",
    "Tall freestanding lamps used indoors to provide ambient or task lighting in living spaces.",
    "Bright, movable floodlights designed for temporary outdoor lighting in work areas or events.",
    "Durable lights used for construction or repair tasks, often including multiple connected bulbs.",
    "Lighting fixtures that automatically turn on during power outages to guide people to safety.",
    "Short, sturdy posts with built-in lights, commonly placed along pathways or driveways for visibility.",
    "Outdoor light fixtures mounted on posts, used in residential gardens or pathways.",
    "Electric-powered lights placed along paths, gardens, or steps to enhance visibility and aesthetics.",
    "Outdoor lighting fixtures installed on porches or patios to improve ambiance and security.",
    "Outdoor lights designed for home security, sometimes including cameras for surveillance.",
    "Special waterproof lighting installed in or around pools and fountains to enhance visibility and aesthetics.",
    "Compact wall-mounted or small floodlights used for exterior or commercial lighting applications.",
    "Ceiling-mounted lighting fixtures that sit close to the ceiling, suitable for low-clearance spaces.",
    "Holders designed for single or multiple light bulbs, often used in fixtures or standalone applications.",
    "Hanging light fixtures suspended from the ceiling, commonly used for task or decorative lighting.",
    "Built-in ceiling lights that are installed within a hollow opening, often requiring separate housing and trims.",
    "Mounted lighting systems with adjustable heads, often used for directional lighting in rooms or galleries.",
    "Lights installed beneath cabinets to illuminate countertops or work areas, commonly in kitchens.",
    "Lighting fixtures attached to walls, such as sconces, used for ambient or decorative lighting.",
    "Elegant, multi-light fixtures often hanging from ceilings, used for decorative lighting in large rooms.",
    "Ceiling-mounted fans that include integrated lighting to provide both airflow and illumination.",
    "Long, flexible lighting strips often used for accent lighting in homes, offices, or display areas.",
    "Long lighting fixtures installed on ceilings, walls, or suspended from above, commonly used in offices or warehouses.",
    "Rectangular or square ceiling fixtures, either built-in or surface-mounted, for commercial lighting.",
    "Flat, energy-efficient LED panels mounted on ceilings or suspended for even light distribution.",
    "Powerful overhead lighting used in large spaces like warehouses or industrial buildings.",
    "Durable lighting solutions installed in parking garages, either on ceilings or walls, for enhanced visibility.",
    "Specialized lights used in theaters, concerts, and events to illuminate performers and set designs.",
    "Street or highway lighting fixtures mounted on poles or arms, used for large-scale public or commercial outdoor illumination.",
    "High-power floodlights used for lighting large outdoor areas such as sports fields, stadiums, and parking lots.",
    "Electrical components used to regulate the current in fluorescent, HID, or other lighting systems."
]

# Ground truth mapping (expected indices of correct matches)
true_indices = list(range(len(new_product_description)))

# Function to evaluate a model using Top-K Accuracy and MRR
def evaluate_model(model_name, k=5):
    print(f"Evaluating Model: {model_name} with k={k}")
    
    # Load the model
    model = SentenceTransformer(model_name)
    
    # Encode existing product descriptions
    description_embeddings = model.encode(existing_product_description, convert_to_tensor=True)
    
    top_k_correct = 0
    mrr_total = 0
    total_queries = len(new_product_description)
    
    # Iterate through each new product
    for i, query in enumerate(new_product_description):
        query_embedding = model.encode(query, convert_to_tensor=True)
        
        # Compute cosine similarity
        similarity_scores = util.pytorch_cos_sim(query_embedding, description_embeddings)[0]
        
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
file_path = "C:/Users/names/OneDrive - Douglas College/Semester 7/Applied Research Project - CSIS4495 002/2. Progress Reports/Progress Report 2/model_evaluation_pd.csv"

# Export DataFrame to CSV
df_results.to_csv(file_path, index=True, mode='w')
print("CSV file has been successfully replaced.")