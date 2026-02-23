import asyncio
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import Base, FoodItem, FoodSource
from app.services.db_service import engine, AsyncSessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Core Global Food Items
GLOBAL_ITEMS = [
    {
        "name": "Egg (Large)",
        "calories_per_100g": 143.0,
        "protein_per_100g": 12.6,
        "fat_per_100g": 9.5,
        "carbs_per_100g": 0.7,
        "serving_size_g": 50.0,
        "serving_name": "Egg"
    },
    {
        "name": "Chicken Breast (Cooked)",
        "calories_per_100g": 165.0,
        "protein_per_100g": 31.0,
        "fat_per_100g": 3.6,
        "carbs_per_100g": 0.0,
        "serving_size_g": 150.0,
        "serving_name": "Piece"
    },
    {
        "name": "Oats (Dry)",
        "calories_per_100g": 389.0,
        "protein_per_100g": 16.9,
        "fat_per_100g": 6.9,
        "carbs_per_100g": 66.3,
        "serving_size_g": 40.0,
        "serving_name": "Cup"
    },
    {
        "name": "Spinach (Raw)",
        "calories_per_100g": 23.0,
        "protein_per_100g": 2.9,
        "fat_per_100g": 0.4,
        "carbs_per_100g": 3.6,
        "serving_size_g": 30.0,
        "serving_name": "Handful"
    },
    {
        "name": "Milk (Whole)",
        "calories_per_100g": 61.0,
        "protein_per_100g": 3.2,
        "fat_per_100g": 3.3,
        "carbs_per_100g": 4.8,
        "serving_size_g": 240.0,
        "serving_name": "Glass"
    },
    {
        "name": "Banana",
        "calories_per_100g": 89.0,
        "protein_per_100g": 1.1,
        "fat_per_100g": 0.3,
        "carbs_per_100g": 22.8,
        "serving_size_g": 120.0,
        "serving_name": "Fruit"
    },
    {
        "name": "Greek Yogurt (Non-fat)",
        "calories_per_100g": 59.0,
        "protein_per_100g": 10.0,
        "fat_per_100g": 0.4,
        "carbs_per_100g": 3.6,
        "serving_size_g": 170.0,
        "serving_name": "Container"
    }
]

async def seed():
    logger.info("Connecting to database and creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Seeding Global Library...")
    async with AsyncSessionLocal() as session:
        for item_data in GLOBAL_ITEMS:
            # Check if it already exists
            from sqlalchemy import select
            stmt = select(FoodItem).where(FoodItem.name == item_data["name"], FoodItem.source == FoodSource.GLOBAL)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                continue
            
            food_item = FoodItem(
                id=uuid.uuid4(),
                name=item_data["name"],
                source=FoodSource.GLOBAL,
                calories_per_100g=item_data["calories_per_100g"],
                protein_per_100g=item_data["protein_per_100g"],
                fat_per_100g=item_data["fat_per_100g"],
                carbs_per_100g=item_data["carbs_per_100g"],
                serving_size_g=item_data.get("serving_size_g"),
                serving_name=item_data.get("serving_name"),
                user_id=None
            )
            session.add(food_item)
        
        await session.commit()
    logger.info("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())
