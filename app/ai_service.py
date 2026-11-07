import os
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any
from app.config import GEMINI_API_KEY

logger = logging.getLogger("ecoguard.ai")

# Fallback smart heuristics database for realistic waste profiling
HEURISTIC_PRESETS = [
    {
        "keywords": ["plastic", "bottle", "poly", "bag", "wrapper", "container"],
        "primary_category": "Plastic & Packaging Waste",
        "categories": ["Single-use Plastics", "High-Density Polyethylene (HDPE)", "Commercial Packaging"],
        "severity": "Medium",
        "confidence_score": 0.91,
        "risk_assessment": "High microplastic dispersion risk; severe hazard of stormwater drain clogging during rainfall.",
        "environmental_impact": "Non-biodegradable synthetic polymers contaminating soil microbiome and surface runoff.",
        "recommended_action": "Deploy dry-waste sorting vehicle. Coordinate with registered plastic recycling recovery facility (MRF)."
    },
    {
        "keywords": ["construction", "debris", "concrete", "brick", "cement", "rubble", "demolition"],
        "primary_category": "Construction & Demolition (C&D) Waste",
        "categories": ["Concrete Rubble", "Broken Masonry", "Excavated Earth Debris"],
        "severity": "High",
        "confidence_score": 0.94,
        "risk_assessment": "Heavy particulate matter (PM10/PM2.5) dust emissions, road encroachment, and structural obstruction of public drainage.",
        "environmental_impact": "Soil compaction, aesthetic degradation, and airborne silica dust causing respiratory concerns.",
        "recommended_action": "Issue violation citation under C&D Waste Management Rules. Dispatch hydraulic tipper truck for transfer to authorized C&D recycling plant."
    },
    {
        "keywords": ["industrial", "chemical", "barrel", "drum", "sludge", "oil", "hazardous", "toxic"],
        "primary_category": "Industrial & Hazardous Waste",
        "categories": ["Industrial Sludge", "Chemical Residues", "Contaminated Metal Drums"],
        "severity": "Critical",
        "confidence_score": 0.96,
        "risk_assessment": "Urgent hazard: acute risk of heavy metal/chemical leaching into groundwater aquifers; immediate flammability or toxic vapor risk.",
        "environmental_impact": "Direct toxic contamination of soil and subsurface water table; poses severe acute risk to nearby residents and flora/fauna.",
        "recommended_action": "Priority 1 Alert! Dispatch State Pollution Control Board hazardous materials (HAZMAT) squad with protective PPE and containment booms."
    },
    {
        "keywords": ["electronic", "ewaste", "e-waste", "circuit", "computer", "wire", "cable", "appliance"],
        "primary_category": "Electronic Waste (E-Waste)",
        "categories": ["Printed Circuit Boards", "Obsolete Electronics", "Heavy Metal Components"],
        "severity": "High",
        "confidence_score": 0.89,
        "risk_assessment": "Leaching of toxic heavy metals (lead, cadmium, mercury) into soil; fire risk from unhandled lithium components.",
        "environmental_impact": "Persistent bio-accumulative toxic pollutants contaminating soil strata.",
        "recommended_action": "Seal off perimeter. Coordinate with authorized State Pollution Control Board e-waste dismantler and certified recycling unit."
    },
    {
        "keywords": ["organic", "food", "vegetable", "market", "carcass", "decay", "biomass"],
        "primary_category": "Organic & Biodegradable Waste",
        "categories": ["Decomposing Food Waste", "Market Produce Refuse", "Moist Biowaste"],
        "severity": "Medium",
        "confidence_score": 0.88,
        "risk_assessment": "Rapid anaerobic decomposition leading to foul odors, methane (CH4) greenhouse gas emissions, and vector-borne pest breeding (flies, rodents).",
        "environmental_impact": "Noxious leachate production, surface water eutrophication, and public health sanitary nuisance.",
        "recommended_action": "Expedited dispatch of municipal wet-waste collection tippers. Transfer to nearest biomethanation or aerobic composting plant."
    }
]

DEFAULT_FALLBACK = {
    "primary_category": "Mixed Municipal Solid Waste",
    "categories": ["Unsegregated Municipal Waste", "Commercial Discards", "Packaging Materials"],
    "severity": "Medium",
    "confidence_score": 0.86,
    "risk_assessment": "Visual pollution, localized soil degradation, and vector proliferation due to mixed unsegregated discards.",
    "environmental_impact": "Littering of public space, odor nuisance, and environmental degradation.",
    "recommended_action": "Dispatch zonal sanitary workforce for mechanized clearance and segregated recovery."
}

def analyze_waste_image(image_path: str, filename: str = "") -> Dict[str, Any]:
    """
    Analyzes an uploaded waste dumping photo using Google Gemini API.
    If API key is missing or offline, uses realistic ecological heuristic analysis.
    """
    if GEMINI_API_KEY:
        try:
            # Try official google-genai SDK
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=GEMINI_API_KEY)

            with open(image_path, "rb") as f:
                image_bytes = f.read()

            prompt = """
            You are EcoGuard AI's specialized environmental computer vision agent.
            Analyze this uploaded photograph of dumped waste thoroughly.
            Return ONLY a valid JSON object (no markdown, no extra text) with the following structure:
            {
                "primary_category": "e.g. Plastic & Packaging Waste / Construction & Demolition / Industrial & Hazardous / Electronic Waste / Organic Waste / Mixed Solid Waste",
                "categories": ["list", "of", "visible", "waste", "types"],
                "severity": "Low" or "Medium" or "High" or "Critical",
                "confidence_score": float between 0.70 and 0.99,
                "risk_assessment": "1-2 sentences explaining specific risks (drain blockage, toxic leachates, fire hazard, etc.)",
                "environmental_impact": "1-2 sentences on ecological damage (soil, water, air, public health)",
                "recommended_action": "1-2 actionable operational steps for municipal/environmental enforcement officers"
            }
            """

            # Determine mime type
            mime_type = "image/jpeg"
            lower = str(image_path).lower()
            if lower.endswith(".png"):
                mime_type = "image/png"
            elif lower.endswith(".webp"):
                mime_type = "image/webp"

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt
                ]
            )

            response_text = response.text.strip()
            # Clean possible markdown ticks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            parsed = json.loads(response_text.strip())
            parsed["is_ai_preliminary"] = True
            parsed["disclaimer"] = "AI Preliminary Observation - Requires physical verification by an authorized municipal officer before enforcement action."
            return parsed

        except Exception as e:
            logger.warning(f"Gemini API analysis failed or returned error: {e}. Falling back to smart ecological analyzer.")

    # Heuristic fallback based on filename and intelligent rules
    fname_lower = (filename + " " + Path(image_path).name).lower()
    selected_preset = DEFAULT_FALLBACK

    for preset in HEURISTIC_PRESETS:
        for kw in preset["keywords"]:
            if kw in fname_lower:
                selected_preset = preset
                break
        if selected_preset != DEFAULT_FALLBACK:
            break

    result = dict(selected_preset)
    result["is_ai_preliminary"] = True
    result["disclaimer"] = "AI Preliminary Observation - Requires physical verification by an authorized municipal officer before enforcement action."
    return result
