import logging
import uuid
from typing import List, Dict, Any

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from app.bot.bot_instance import bot
from app.models.schemas import User, Log, FoodItem, FoodSource
from app.services.db_service import AsyncSessionLocal
from app.services.gemini_nlp import parse_food_log, analyze_food_image
from app.services.matcher import match_food_item, calculate_macros

from aiogram.filters import Command
from app.services.dish_service import get_dish_macros

logger = logging.getLogger(__name__)
router = Router()

class LoggingState(StatesGroup):
    confirming_log = State()
    waiting_for_manual_name = State()
    waiting_for_manual_cals = State()
    waiting_for_manual_protein = State()

@router.message(Command("log_dish"))
async def cmd_log_dish(message: types.Message):
    """
    Lists all dishes for the user to log.
    """
    async with AsyncSessionLocal() as db:
        # Get User
        stmt = (
            select(Dish)
            .join(User)
            .where(User.telegram_id == message.from_user.id)
        )
        result = await db.execute(stmt)
        dishes = result.scalars().all()

        if not dishes:
            await message.answer("❌ You don't have any saved dishes yet. Create one via the dashboard!")
            return

        builder = InlineKeyboardBuilder()
        for dish in dishes:
            builder.button(text=dish.name, callback_data=f"log_dish_{dish.id}")
        
        builder.adjust(1)
        await message.answer("🍽️ Select a dish to log:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("log_dish_"))
async def handle_log_dish_cb(callback: types.CallbackQuery):
    """
    Logs the selected dish and snapshots its macros.
    """
    dish_id = uuid.UUID(callback.data[len("log_dish_"):])
    
    async with AsyncSessionLocal() as db:
        # 1. Fetch User
        stmt = select(User).where(User.telegram_id == callback.from_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        # 2. Get Dish Macros (The "Immutable" Snapshot)
        stmt_dish = select(Dish).where(Dish.id == dish_id)
        res_dish = await db.execute(stmt_dish)
        dish = res_dish.scalar_one_or_none()
        
        if not dish:
            await callback.answer("Dish not found.")
            return

        macros = await get_dish_macros(db, dish_id)

        # 3. Save Log
        log_entry = Log(
            user_id=user.id,
            display_name=dish.name,
            total_calories=macros["calories"],
            total_protein=macros["protein"],
            total_fat=macros["fat"],
            total_carbs=macros["carbs"],
            original_type="dish",
            original_id=dish.id
        )
        db.add(log_entry)
        await db.commit()

    await callback.message.edit_text(f"✅ Logged dish: **{dish.name}**\n🔥 {macros['calories']:.0f} kcal | 🥩 {macros['protein']:.1f}g P", parse_mode="Markdown")
    await callback.answer()

@router.message(F.text == "📝 Manual Entry")
async def start_manual_log(message: types.Message, state: FSMContext):
    await state.set_state(LoggingState.waiting_for_manual_name)
    await message.answer("What are you logging? (e.g., 'Mystery Protein Bar')")

@router.message(LoggingState.waiting_for_manual_name)
async def process_manual_name(message: types.Message, state: FSMContext):
    await state.update_data(manual_name=message.text)
    await state.set_state(LoggingState.waiting_for_manual_cals)
    await message.answer(f"How many calories in '{message.text}'?")

@router.message(LoggingState.waiting_for_manual_cals)
async def process_manual_cals(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Please enter a number for calories.")
        return
    await state.update_data(manual_cals=float(message.text))
    await state.set_state(LoggingState.waiting_for_manual_protein)
    await message.answer("How many grams of protein?")

@router.message(LoggingState.waiting_for_manual_protein)
async def process_manual_protein(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '', 1).isdigit():
        await message.answer("Please enter a number for protein.")
        return
    
    user_data = await state.get_data()
    name = user_data['manual_name']
    cals = user_data['manual_cals']
    protein = float(message.text)

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        log_entry = Log(
            user_id=user.id,
            display_name=name,
            total_calories=cals,
            total_protein=protein,
            total_fat=0.0, # Optional: could add more states for these
            total_carbs=0.0,
            original_type="manual_override"
        )
        db.add(log_entry)
        await db.commit()

    await message.answer(f"✅ Logged: {name} ({cals:.0f} kcal, {protein:.1f}g P)")
    await state.clear()

@router.message(F.text)
async def handle_text_log(message: types.Message, state: FSMContext):
    query = message.text
    status_msg = await message.answer(f"🔍 Parsing: \"{query}\"...")

    parsed_items = await parse_food_log(query)
    if not parsed_items:
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 Manual Entry", callback_data="start_manual")
        await status_msg.edit_text("❌ I couldn't parse that. Want to enter it manually?", reply_markup=builder.as_markup())
        return

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            await status_msg.edit_text("❌ User not found. Run /start first.")
            return

        final_logs = []
        summary_text = "🍽️ **Proposed Log:**\n\n"
        total_cals = 0.0

        for p_item in parsed_items:
            db_item = await match_food_item(db, user.id, p_item['item'])
            if db_item:
                macros = calculate_macros(db_item, p_item['amount'], p_item['unit'])
                total_cals += macros['calories']
                summary_text += f"✅ **{db_item.name}**\n   - {p_item['amount']} {p_item['unit']}\n   - 🔥 {macros['calories']:.0f} kcal\n\n"
                final_logs.append({
                    "display_name": db_item.name, "total_calories": macros['calories'],
                    "total_protein": macros['protein'], "total_fat": macros['fat'],
                    "total_carbs": macros['carbs'], "original_type": "item", "original_id": str(db_item.id)
                })
            else:
                summary_text += f"⚠️ **{p_item['item']}** (Not found)\n\n"

        if not final_logs:
            builder = InlineKeyboardBuilder()
            builder.button(text="📝 Manual Entry", callback_data="start_manual")
            await status_msg.edit_text("❌ No matches found. Try manual entry?", reply_markup=builder.as_markup())
            return

        summary_text += f"**Total: {total_cals:.0f} kcal**\n\nCorrect?"
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Confirm", callback_data="confirm_log")
        builder.button(text="📝 Manual Override", callback_data="start_manual")
        builder.button(text="❌ Cancel", callback_data="cancel_log")
        
        await state.update_data(pending_logs=final_logs)
        await state.set_state(LoggingState.confirming_log)
        await status_msg.edit_text(summary_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data == "start_manual")
async def cb_start_manual(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(LoggingState.waiting_for_manual_name)
    await callback.message.answer("What are you logging? (e.g., 'Mystery Protein Bar')")
    await callback.answer()

@router.callback_query(F.data == "confirm_log", StateFilter(LoggingState.confirming_log))
async def confirm_log_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pending_logs = data.get("pending_logs", [])
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.telegram_id == callback.from_user.id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        for log_data in pending_logs:
            db.add(Log(
                user_id=user.id, display_name=log_data["display_name"],
                total_calories=log_data["total_calories"], total_protein=log_data["total_protein"],
                total_fat=log_data["total_fat"], total_carbs=log_data["total_carbs"],
                original_type=log_data["original_type"],
                original_id=uuid.UUID(log_data["original_id"]) if log_data.get("original_id") else None
            ))
        await db.commit()
    await callback.message.edit_text("✅ Logged! Keep up the good work.")
    await state.clear()

@router.callback_query(F.data == "cancel_log")
async def cancel_log_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Log cancelled.")
    await state.clear()
