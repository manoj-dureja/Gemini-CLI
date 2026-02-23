from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import User, Log
from app.services.db_service import get_db
from app.services.log_service import get_day_start_local

router = APIRouter()

@router.get("/analytics")
async def get_analytics(
    telegram_id: int, 
    range_type: str = Query("daily", regex="^(daily|weekly)$"), 
    db: AsyncSession = Depends(get_db)
):
    """
    Returns daily/weekly macro-composition for a user.
    """
    # 1. Fetch User
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return {"error": "User not found"}

    # 2. Determine Timeframe (FIXED)
    if range_type == "daily":
        start_time = get_day_start_local() # Midnight in LOCAL timezone
    else:  # weekly
        start_time = datetime.now(timezone.utc) - timedelta(days=7)

    # 3. Aggregate Logs
    stmt = select(
        func.sum(Log.total_calories).label("calories"),
        func.sum(Log.total_protein).label("protein"),
        func.sum(Log.total_fat).label("fat"),
        func.sum(Log.total_carbs).label("carbs")
    ).where(
        Log.user_id == user.id,
        Log.log_time >= start_time
    )

    result = await db.execute(stmt)
    totals = result.one_or_none()

    # 4. Return results with goal progress
    return {
        "user": user.username,
        "range": range_type,
        "totals": {
            "calories": totals.calories or 0,
            "protein": totals.protein or 0,
            "fat": totals.fat or 0,
            "carbs": totals.carbs or 0
        },
        "goals": {
            "calories": user.daily_calorie_goal,
            "protein": user.daily_protein_goal_g
        },
        "progress": {
            "calories": (totals.calories / user.daily_calorie_goal) if totals.calories and user.daily_calorie_goal else 0
        }
    }
