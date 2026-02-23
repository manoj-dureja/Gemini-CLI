import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.schemas import User, FoodItem, Log, Dish, DishIngredient
from app.services.db_service import get_db
from app.services.gemini_nlp import parse_food_log

router = APIRouter()

class StructuredEntry(BaseModel):
    food_item_id: Optional[uuid.UUID] = None
    dish_id: Optional[uuid.UUID] = None
    quantity: float
    unit: str  # 'g' or 'count'

class LogFoodRequest(BaseModel):
    user_telegram_id: int
    input_type: str  # 'nlp', 'structured', 'manual'
    text_query: Optional[str] = None
    structured_entry: Optional[StructuredEntry] = None

@router.post("/log_food")
async def log_food(request: LogFoodRequest, db: AsyncSession = Depends(get_db)):
    """
    Handles logging food from both structured and NLP inputs.
    """
    # 1. Fetch User
    stmt = select(User).where(User.telegram_id == request.user_telegram_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.input_type == "nlp" and request.text_query:
        # Use Gemini Parser logic
        parsed_items = await parse_food_log(request.text_query)
        if not parsed_items:
            raise HTTPException(status_code=400, detail="Could not parse NLP query")
        
        # NOTE: For brevity, this currently just logs the intention. 
        # Real-world matching against Global_Library/User_Customs is the next layer.
        return {"msg": "NLP results processed (pending library match)", "parsed": parsed_items}

    elif request.input_type == "structured" and request.structured_entry:
        entry = request.structured_entry
        
        # 2. Logic for Food Item
        if entry.food_item_id:
            stmt = select(FoodItem).where(FoodItem.id == entry.food_item_id)
            result = await db.execute(stmt)
            item = result.scalar_one_or_none()
            if not item:
                raise HTTPException(status_code=404, detail="Food item not found")

            # 3. Calculate Macros (scaling logic)
            scale = entry.quantity / 100.0 if entry.unit == 'g' else entry.quantity
            
            # 4. Snapshot to Logs (Immutable Rule)
            log_entry = Log(
                user_id=user.id,
                display_name=item.name,
                total_calories=item.calories_per_100g * scale,
                total_protein=item.protein_per_100g * scale,
                total_fat=item.fat_per_100g * scale,
                total_carbs=item.carbs_per_100g * scale,
                original_type="item",
                original_id=item.id,
                raw_input_text=request.text_query
            )
            db.add(log_entry)
            await db.commit()
            return {"msg": "Food logged successfully", "calories": log_entry.total_calories}

    raise HTTPException(status_code=400, detail="Invalid log request")
