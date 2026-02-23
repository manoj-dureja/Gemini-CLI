import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class FoodSource(PyEnum):
    GLOBAL = "global"
    CUSTOM = "custom"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(Text)
    daily_calorie_goal: Mapped[int] = mapped_column(default=2000)
    daily_protein_goal_g: Mapped[int] = mapped_column(default=150)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    food_items: Mapped[List["FoodItem"]] = relationship(back_populates="user")
    dishes: Mapped[List["Dish"]] = relationship(back_populates="user")
    logs: Mapped[List["Log"]] = relationship(back_populates="user")


class FoodItem(Base):
    __tablename__ = "food_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[FoodSource] = mapped_column(Enum(FoodSource), nullable=False)
    calories_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    protein_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    serving_size_g: Mapped[Optional[float]] = mapped_column(Float)
    serving_name: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped[Optional["User"]] = relationship(back_populates="food_items")
    dish_ingredients: Mapped[List["DishIngredient"]] = relationship(back_populates="food_item")


class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # Soft Delete
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("dishes.id")) # For Versioning
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="dishes")
    ingredients: Mapped[List["DishIngredient"]] = relationship(back_populates="dish", cascade="all, delete-orphan")


class DishIngredient(Base):
    __tablename__ = "dish_ingredients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dish_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    food_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("food_items.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)  # 'g' or 'count'

    dish: Mapped["Dish"] = relationship(back_populates="ingredients")
    food_item: Mapped["FoodItem"] = relationship(back_populates="dish_ingredients")


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    log_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Snapshotted Data (Immutable Rule)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    total_calories: Mapped[float] = mapped_column(Float, nullable=False)
    total_protein: Mapped[float] = mapped_column(Float, nullable=False)
    total_fat: Mapped[float] = mapped_column(Float, nullable=False)
    total_carbs: Mapped[float] = mapped_column(Float, nullable=False)

    # Metadata
    original_type: Mapped[Optional[str]] = mapped_column(Text)  # 'dish', 'item', or 'manual_override'
    original_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    raw_input_text: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="logs")
