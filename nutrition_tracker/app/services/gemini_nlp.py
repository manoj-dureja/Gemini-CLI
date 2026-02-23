import json
import logging
import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from pydantic import BaseModel, Field

from app.core.config import settings

# Configure Logging
logger = logging.getLogger(__name__)

# Initialize Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

# Define the structured output model
class ParsedFoodItem(BaseModel):
    item: str = Field(description="The name of the food item")
    amount: float = Field(description="The numeric quantity/amount")
    unit: str = Field(description="The unit of measurement (e.g., 'g', 'ml', 'cup', 'slice', 'count')")

class FoodLogResponse(BaseModel):
    items: List[ParsedFoodItem]

# System Instruction
SYSTEM_PROMPT = """
You are a specialized nutrition assistant for a high-precision food logging app.
Your task is to parse natural language food logs into a structured JSON format.

RULES:
1. Parse the input string into individual food items.
2. For each item, identify the:
   - 'item': The name of the food (e.g., "egg", "oats", "milk").
   - 'amount': The numeric quantity. If no amount is provided, assume 1.0.
   - 'unit': The unit of measurement. Use 'count' for discrete items like "eggs" or "apples". Use 'g' for grams, 'ml' for milliliters.
3. If multiple items are mentioned, provide them as a list.
4. Return ONLY a valid JSON object matching the requested schema. No conversational filler.

Example 1: "2 eggs and 100g oats"
Output: {"items": [{"item": "egg", "amount": 2.0, "unit": "count"}, {"item": "oats", "amount": 100.0, "unit": "g"}]}

Example 2: "a cup of milk and a banana"
Output: {"items": [{"item": "milk", "amount": 1.0, "unit": "cup"}, {"item": "banana", "amount": 1.0, "unit": "count"}]}
"""

async def parse_food_log(query: str) -> Optional[List[Dict[str, Any]]]:
    """
    Uses Gemini 1.5 Flash to parse a natural language query into structured JSON.
    """
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.")
        return None

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "response_mime_type": "application/json",
            },
            system_instruction=SYSTEM_PROMPT
        )
        
        response = await model.generate_content_async(query)
        
        # Parse the JSON response
        data = json.loads(response.text)
        
        # Validate with Pydantic
        validated_data = FoodLogResponse(**data)
        
        return [item.model_dump() for item in validated_data.items]
        
    except Exception as e:
        logger.error(f"Error parsing food log with Gemini: {e}")
        return None

async def analyze_food_image(image_bytes: bytes) -> Optional[List[Dict[str, Any]]]:
    """
    Uses Gemini 1.5 Flash Vision to identify food items in an image.
    """
    if not settings.GEMINI_API_KEY:
        return None

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "response_mime_type": "application/json",
            },
            system_instruction=SYSTEM_PROMPT + "
Note: You are analyzing an image. Identify the items and estimate their quantities."
        )
        
        # Prepare the image part
        image_parts = [{"mime_type": "image/jpeg", "data": image_bytes}]
        
        response = await model.generate_content_async(["What is in this meal? Provide a structured list.", image_parts[0]])
        
        data = json.loads(response.text)
        validated_data = FoodLogResponse(**data)
        
        return [item.model_dump() for item in validated_data.items]

    except Exception as e:
        logger.error(f"Error analyzing food image with Gemini: {e}")
        return None
