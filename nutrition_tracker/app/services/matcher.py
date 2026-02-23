import logging
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import FoodItem, FoodSource

logger = logging.getLogger(__name__)

async def match_food_item(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    name: str
) -> Optional[FoodItem]:
    """
    Finds the best match for a food name.
    Priority: User's custom items > Global library.
    """
    # Simple case-insensitive ILIKE search
    # In a production app, you might use pg_trgm for true fuzzy matching.
    stmt = (
        select(FoodItem)
        .where(
            or_(
                FoodItem.user_id == user_id,
                FoodItem.source == FoodSource.GLOBAL
            ),
            FoodItem.name.ilike(f"%{name}%"),
            FoodItem.is_active == True
        )
        .order_by(FoodItem.user_id.desc_nulls_last()) # User items first
        .limit(1)
    )
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

def calculate_macros(item: FoodItem, amount: float, unit: str) -> Dict[str, float]:
    """
    Calculates total macros based on the item's density and the user's unit.
    """
    # 1. Determine weight in grams
    weight_g = 0.0
    
    if unit.lower() in ['g', 'grams']:
        weight_g = amount
    elif unit.lower() in ['count', 'serving', 'piece', item.serving_name.lower() if item.serving_name else '']:
        if item.serving_size_g:
            weight_g = amount * item.serving_size_g
        else:
            # Fallback: if no serving size is defined, treat amount as 100g units 
            # (risky, but common in simplified DBs)
            weight_g = amount * 100.0 
    else:
        # Default to 100g units if unknown unit
        weight_g = amount * 100.0

    # 2. Scale macros (stored per 100g)
    multiplier = weight_g / 100.0
    
    return {
        "calories": item.calories_per_100g * multiplier,
        "protein": item.protein_per_100g * multiplier,
        "fat": item.fat_per_100g * multiplier,
        "carbs": item.carbs_per_100g * multiplier,
        "weight_g": weight_g
    }
