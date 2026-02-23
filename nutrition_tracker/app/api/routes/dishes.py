import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.schemas import User, Dish, DishIngredient, FoodItem
from app.services.db_service import get_db

router = APIRouter()

class IngredientEntry(BaseModel):
    food_item_id: uuid.UUID
    quantity: float
    unit: str  # 'g' or 'count'

class DishCreate(BaseModel):
    user_telegram_id: int
    name: str
    description: Optional[str] = None
    ingredients: List[IngredientEntry]

class DishResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]

@router.post("/dishes")
async def create_dish(request: DishCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates a new composite dish for a user.
    """
    stmt = select(User).where(User.telegram_id == request.user_telegram_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_dish = Dish(
        user_id=user.id,
        name=request.name,
        description=request.description
    )
    db.add(new_dish)
    await db.flush() # Get the new_dish.id

    for ing in request.ingredients:
        new_ing = DishIngredient(
            dish_id=new_dish.id,
            food_item_id=ing.food_item_id,
            quantity=ing.quantity,
            unit=ing.unit
        )
        db.add(new_ing)
    
    await db.commit()
    return {"msg": "Dish created successfully", "dish_id": new_dish.id}

@router.get("/dishes")
async def list_dishes(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """
    Lists all dishes for a specific user.
    """
    stmt = (
        select(Dish)
        .join(User)
        .where(User.telegram_id == telegram_id)
        .options(selectinload(Dish.ingredients))
    )
    result = await db.execute(stmt)
    dishes = result.scalars().all()
    return dishes

@router.delete("/dishes/{dish_id}")
async def delete_dish(dish_id: uuid.UUID, telegram_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes a specific dish.
    """
    # Verify ownership before delete
    stmt = (
        select(Dish)
        .join(User)
        .where(Dish.id == dish_id, User.telegram_id == telegram_id)
    )
    result = await db.execute(stmt)
    dish = result.scalar_one_or_none()
    if not dish:
        raise HTTPException(status_code=403, detail="Unauthorized or dish not found")

    await db.delete(dish)
    await db.commit()
    return {"msg": "Dish deleted"}
