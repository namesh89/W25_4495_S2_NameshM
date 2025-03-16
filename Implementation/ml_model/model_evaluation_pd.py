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
    "Covers all sizes and brightness levels of fluorescent tubes, including uniquely shaped ones and those designed for UV-A and UV-B applications.",
    "Compact fluorescent bulbs intended as replacements for traditional incandescent light bulbs, available in different wattages and socket types, including screw-in induction lamps.",
    "Energy-efficient LED bulbs designed to replace CFLs, incandescent, or halogen lights, featuring a range of wattages and both pin-type and screw-in bases.",
    "Versatile LED tubes available in various lengths and forms, suitable for general, industrial, and specialty lighting, including high-intensity discharge replacements.",
    "Includes mercury-containing HID technologies such as High-Pressure Sodium, Low-Pressure Sodium, Metal Halide, and Mercury Vapor lamps, as well as UV-C sterilization lamps, tubular induction, and neon replacements.",
    "Traditional filament bulbs in multiple shapes, sizes, and wattage levels, commonly used for decorative or functional illumination.",
    "Small-sized bulbs, including LED, halogen, incandescent, and neon types, widely used in applications such as flashlights, signage, emergency lighting, vehicle indicators, and decorative strips.",
    "Compact, portable book lights designed for reading, including those meant for e-readers such as Kindle devices.",
    "Flexible, adjustable snake lights ideal for task lighting in various settings.",
    "LED or battery-powered bike lights designed for visibility and safety in low-light conditions.",
    "Portable lighting solutions such as flashlights, headlamps, and handheld spotlights used for camping, emergency, and outdoor applications.",
    "Clip-on spotlights and lamps that provide adjustable lighting for desks, workstations, or reading areas.",
    "Standalone lamp-holders designed to accommodate a single bulb for focused or ambient lighting.",
    "Battery-operated or electric lanterns and candle-like lights, providing portable and decorative illumination.",
    "Night lights designed to provide low-level illumination for bedrooms, hallways, and nurseries.",
    "Remote-controlled track lighting heads for egress and emergency lighting applications.",
    "Battery-powered lights designed for use in closets and utility spaces where permanent lighting is unavailable.",
    "Water-resistant lights designed for pools, ponds, and bathtubs, operating on battery power for safe submersion.",
    "Compact circular or oval LED lights, often recessed or surface-mounted, used for under-cabinet or display lighting, typically under 4 inches in diameter.",
    "Solar-powered outdoor lights designed to illuminate pathways, gardens, and steps, enhancing both safety and aesthetics.",
    "Holiday and decorative light strings, categorized and charged based on the number of lights per strand for recycling purposes.",
    "Flexible LED rope, tape, or strip lights, sold in increments of 10 meters, commonly used for accent lighting or signage.",
    "Interconnected outdoor stake lights designed to provide ambient pathway illumination in gardens or along walkways.",
    "Adjustable and compact desk lamps used for reading, studying, or workspace lighting.",
    "Tabletop lamps designed for general home or office use, often featuring decorative designs and adjustable brightness.",
    "Freestanding floor lamps, available in various styles, used for ambient or task lighting in living spaces.",
    "Portable high-powered floodlights suitable for temporary outdoor lighting, construction sites, or emergency situations.",
    "String-based work lights used to illuminate large areas in construction zones, workshops, or outdoor workspaces.",
    "Emergency and egress lighting fixtures designed for safety applications in commercial and residential buildings.",
    "Short post lights, commonly used in driveways, pathways, and landscaping for decorative and functional lighting.",
    "Post-mounted lighting fixtures intended for residential outdoor applications such as front yards or patios.",
    "Outdoor garden and pathway lights that are powered through traditional electrical wiring rather than solar energy.",
    "Porch and patio lights designed to provide illumination and aesthetic appeal for outdoor seating areas.",
    "Residential-grade security floodlights, some featuring integrated motion sensors and surveillance cameras.",
    "Underwater lighting solutions designed for pools, fountains, and water features, enhancing nighttime aesthetics.",
    "Compact wall-mounted floodlights, including those used for commercial or security applications below 250 watts.",
    "Flush-mounted and semi-flush ceiling lights used for low-profile, general indoor lighting applications.",
    "Lamp-holders designed to accommodate multiple bulbs, providing flexible lighting solutions.",
    "Pendant lighting fixtures, suspended from the ceiling, often used for decorative or task lighting.",
    "Recessed lighting fixtures, where fees are applicable only for the housing if trims and other parts are sold separately.",
    "Fixed track lighting and canopy-mounted fixtures used to provide directional or accent lighting in various spaces.",
    "Under-cabinet lighting fixtures, including LED strips and linear fluorescent models for kitchen or workspace illumination.",
    "Wall-mounted sconces designed to provide ambient lighting while enhancing room decor.",
    "Elegant chandelier lighting fixtures, often featuring multiple bulbs, glass, or crystal elements.",
    "Ceiling fans with integrated lighting solutions, providing both air circulation and illumination.",
    "LED strip lighting solutions used for under-cabinet, accent, or commercial display illumination.",
    "Linear lighting fixtures designed for surface mounting, suspension, or wall-mount applications.",
    "Troffer lighting, available in recessed and non-recessed models, commonly used in commercial spaces and offices.",
    "Flat LED panel lighting fixtures, available in surfaced and suspended mounting options for modern indoor lighting.",
    "High and low bay lighting fixtures used in warehouses, industrial spaces, and large commercial areas.",
    "Ceiling and wall-mounted parking garage lights, designed for consistent and durable illumination in parking structures.",
    "Stage lighting fixtures used for theater, concerts, and entertainment venues, providing controlled and focused illumination.",
    "Streetlights and area lighting fixtures, including pole-mounted luminaires for sidewalks, highways, and pathways.",
    "High-wattage floodlights and sports lighting fixtures, designed for large outdoor areas such as stadiums and industrial yards.",
    "Lighting ballasts of all types, including compact fluorescent, electronic, HID, and magnetic ballasts, used for regulating current flow in lighting systems."
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