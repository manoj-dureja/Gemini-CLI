import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import zoneinfo

from app.models.schemas import User, Log, FoodItem, Dish
from app.services.gemini_nlp import parse_food_log
from app.services.matcher import match_food_item, calculate_macros
from app.services.dish_service import get_dish_macros
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_now_local() -> datetime:
    """Returns current time in the configured app timezone."""
    tz = zoneinfo.ZoneInfo(settings.APP_TIMEZONE)
    return datetime.now(tz)

def get_day_start_local() -> datetime:
    """Returns the start of today (00:00:00) in local timezone as UTC-aware datetime."""
    now = get_now_local()
    local_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_start.astimezone(timezone.utc)

async def create_log_from_text(db: AsyncSession, user: User, query: str) -> List[Dict[str, Any]]:
    """
    Core Logic: NLP -> Match -> Calculate -> Snapshot.
    Returns list of prepared log data.
    """
    parsed_items = await parse_food_log(query)
    if not parsed_items:
        return []

    logs_to_create = []
    for p_item in parsed_items:
        db_item = await match_food_item(db, user.id, p_item['item'])
        if db_item:
            macros = calculate_macros(db_item, p_item['amount'], p_item['unit'])
            logs_to_create.append({
                "display_name": db_item.name,
                "total_calories": macros['calories'],
                "total_protein": macros['protein'],
                "total_fat": macros['fat'],
                "total_carbs": macros['carbs'],
                "original_type": "item",
                "original_id": db_item.id
            })
    return logs_to_create

async def persist_logs(db: AsyncSession, user_id: uuid.UUID, log_entries: List[Dict[str, Any]]):
    """Saves snapshotted logs to DB."""
    for entry in log_entries:
        new_log = Log(
            user_id=user_id,
            display_name=entry["display_name"],
            total_calories=entry["total_calories"],
            total_protein=entry["total_protein"],
            total_fat=entry["total_fat"],
            total_carbs=entry["total_carbs"],
            original_type=entry["original_type"],
            original_id=entry.get("original_id"),
            log_time=datetime.now(timezone.utc) # Store as UTC always
        )
        db.add(new_log)
    await db.commit()
