from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import User, Log
from app.services.db_service import AsyncSessionLocal
from datetime import datetime, timezone

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """
    Handles /start and registers the user if they don't exist.
    """
    async with AsyncSessionLocal() as session:
        # Check if user exists
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username or str(message.from_user.id)
            )
            session.add(user)
            await session.commit()
            welcome_msg = f"Welcome, {user.username}! I'm your Bespoke Nutrition Tracker.\n\nCommands:\n/set_goals <cals> <protein> - Set daily targets\n/profile - View your progress\n/log_dish - Log a saved dish\nOr just tell me what you ate!"
        else:
            welcome_msg = f"Welcome back, {user.username}! What have you eaten today?"

        await message.answer(welcome_msg)

@router.message(Command("set_goals"))
async def cmd_set_goals(message: types.Message):
    """
    Updates user goals. Usage: /set_goals 2000 150
    """
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Usage: `/set_goals <calories> <protein_g>`\nExample: `/set_goals 2500 180`", parse_mode="Markdown")
        return

    try:
        cals = int(args[1])
        protein = int(args[2])
    except ValueError:
        await message.answer("Please provide numeric values for goals.")
        return

    async with AsyncSessionLocal() as session:
        stmt = update(User).where(User.telegram_id == message.from_user.id).values(
            daily_calorie_goal=cals,
            daily_protein_goal_g=protein
        )
        await session.execute(stmt)
        await session.commit()

    await message.answer(f"✅ Goals updated!\n🔥 Calories: {cals} kcal\n🥩 Protein: {protein}g")

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    """
    Displays user profile and today's progress.
    """
    async with AsyncSessionLocal() as session:
        # Get User
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer("User not found. Run /start first.")
            return

        # Get Today's Totals
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        from sqlalchemy import func
        stmt_logs = select(
            func.sum(Log.total_calories).label("cals"),
            func.sum(Log.total_protein).label("protein")
        ).where(Log.user_id == user.id, Log.log_time >= today_start)
        
        res_logs = await session.execute(stmt_logs)
        totals = res_logs.one_or_none()
        
        curr_cals = totals.cals or 0
        curr_protein = totals.protein or 0

        msg = (
            f"👤 **{user.username}**\n\n"
            f"🎯 **Daily Goals:**\n"
            f"- Calories: {user.daily_calorie_goal} kcal\n"
            f"- Protein: {user.daily_protein_goal_g}g\n\n"
            f"📊 **Today's Progress:**\n"
            f"- 🔥 {curr_cals:.0f} / {user.daily_calorie_goal} kcal\n"
            f"- 🥩 {curr_protein:.1f} / {user.daily_protein_goal_g}g P\n"
        )
        
        await message.answer(msg, parse_mode="Markdown")
