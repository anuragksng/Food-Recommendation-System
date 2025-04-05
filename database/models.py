from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, create_engine, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)  # In a real app, this would be hashed
    age = Column(String(20))
    gender = Column(String(20))
    dietary_preference = Column(String(50))
    allergies = Column(String(200))
    
    # Relationships
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username='{self.username}', age='{self.age}', dietary_preference='{self.dietary_preference}')>"


class UserPreference(Base):
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    weather_type = Column(String(20), nullable=False)
    spice_preference = Column(Integer)
    sugar_preference = Column(Integer)
    meal_type = Column(String(20))
    recent_dislikes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, weather_type='{self.weather_type}', spice={self.spice_preference}, sugar={self.sugar_preference})>"


class Food(Base):
    __tablename__ = 'foods'
    
    id = Column(Integer, primary_key=True)
    dish_name = Column(String(100), nullable=False)
    cuisine_type = Column(String(50))
    veg_non = Column(String(20))
    description = Column(Text)
    spice_level = Column(Integer)
    sugar_level = Column(Integer)
    dish_category = Column(String(50))
    weather_type = Column(String(20))
    
    # Relationships
    ratings = relationship("Rating", back_populates="food", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Food(id={self.id}, dish_name='{self.dish_name}', cuisine_type='{self.cuisine_type}')>"


class Rating(Base):
    __tablename__ = 'ratings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    food_id = Column(Integer, ForeignKey('foods.id', ondelete='CASCADE'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-10 scale
    
    # Relationships
    user = relationship("User", back_populates="ratings")
    food = relationship("Food", back_populates="ratings")
    
    def __repr__(self):
        return f"<Rating(user_id={self.user_id}, food_id={self.food_id}, rating={self.rating})>"


class LikedDislikedFood(Base):
    __tablename__ = 'liked_disliked_foods'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    food_id = Column(Integer, ForeignKey('foods.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(10), nullable=False)  # 'liked' or 'disliked'
    
    def __repr__(self):
        return f"<LikedDislikedFood(user_id={self.user_id}, food_id={self.food_id}, status='{self.status}')>"


class SearchHistory(Base):
    __tablename__ = 'search_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    search_term = Column(String(100), nullable=False)
    timestamp = Column(Float, nullable=False)  # Unix timestamp
    
    def __repr__(self):
        return f"<SearchHistory(user_id={self.user_id}, search_term='{self.search_term}')>"


class Weather(Base):
    __tablename__ = 'weather'
    
    id = Column(Integer, primary_key=True)
    weather_type = Column(String(20), nullable=False)
    preferred_foods = Column(Text)  # Comma-separated list
    
    def __repr__(self):
        return f"<Weather(weather_type='{self.weather_type}')>"