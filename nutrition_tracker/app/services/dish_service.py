import uuid
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import Dish, DishIngredient, FoodItem, Log

async def get_dish_macros(db: AsyncSession, dish_id: uuid.UUID) -> Dict[str, float]:
    """
    Calculates the total macros for a composite dish by summing its ingredients.
    """
    stmt = (
        select(Dish)
        .options(selectinload(Dish.ingredients).selectinload(DishIngredient.food_item))
        .where(Dish.id == dish_id)
    )
    result = await db.execute(stmt)
    dish = result.scalar_one_or_none()
    
    if not dish:
        return {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}

    totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    
    for ing in dish.ingredients:
        item = ing.food_item
        # Scale macros (stored per 100g)
        scale = ing.quantity / 100.0 if ing.unit == 'g' else ing.quantity * (item.serving_size_g / 100.0 if item.serving_size_g else 1.0)
        
        totals["calories"] += item.calories_per_100g * scale
        totals["protein"] += item.protein_per_100g * scale
        totals["fat"] += item.fat_per_100g * scale
        totals["carbs"] += item.carbs_per_100g * scale
        
    return totals
