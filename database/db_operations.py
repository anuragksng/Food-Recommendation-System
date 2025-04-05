import os
import pandas as pd
import time
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from database.models import Base, User, UserPreference, Food, Rating, LikedDislikedFood, SearchHistory, Weather
from database.db_config import get_db_engine, get_session_factory

# Get the database engine and session factory
engine = get_db_engine()
Session = get_session_factory()

def init_db():
    """Initialize the database by creating all tables"""
    Base.metadata.create_all(engine)
    print("Database tables created")

def import_initial_data():
    """Import data from CSV files into the database"""
    # Check if we've already imported data (check if users table has records)
    session = Session()
    user_count = session.query(User).count()
    
    if user_count > 0:
        print("Data already imported, skipping import")
        session.close()
        return
    
    try:
        # Import users
        df_user = pd.read_csv("attached_assets/user.csv")
        for _, row in df_user.iterrows():
            user = User(
                id=int(row['User_ID']),
                username=f"user{row['User_ID']}",  # Generate username
                password=f"user{row['User_ID']}",  # Default password (should be hashed in a real app)
                age=row['Age'],
                gender=row['Gender'],
                dietary_preference=row['Dietary_Preferences'],
                allergies=row['Allergies'] if not pd.isna(row['Allergies']) else "None"
            )
            session.add(user)
        
        # Import user preferences
        df_user_preferences = pd.read_csv("attached_assets/user_preferences.csv")
        for _, row in df_user_preferences.iterrows():
            pref = UserPreference(
                user_id=int(row['User_ID']),
                weather_type=row['Weather_Type'],
                spice_preference=int(row['Spice_Preference']),
                sugar_preference=int(row['Sugar_Preference']),
                meal_type=row['Meal_Type'],
                recent_dislikes=row['Recent_Dislikes'] if not pd.isna(row['Recent_Dislikes']) else None
            )
            session.add(pref)
        
        # Import foods
        df_food = pd.read_csv("attached_assets/food.csv")
        for _, row in df_food.iterrows():
            food = Food(
                id=int(row['Food_ID']),
                dish_name=row['Dish_Name'],
                cuisine_type=row['Cuisine_Type'],
                veg_non=row['Veg_Non'],
                description=row['Describe'] if not pd.isna(row['Describe']) else "No description available",
                spice_level=int(row['Spice_Level']),
                sugar_level=int(row['Sugar_Level']),
                dish_category=row['Dish_Category'],
                weather_type=row['Weather_Type']
            )
            session.add(food)
        
        # Import ratings
        df_ratings = pd.read_csv("attached_assets/ratings.csv")
        for _, row in df_ratings.iterrows():
            # Handle potential NaN values
            if pd.isna(row['User_ID']) or pd.isna(row['Food_ID']) or pd.isna(row['Rating']):
                continue
                
            rating = Rating(
                user_id=int(row['User_ID']),
                food_id=int(row['Food_ID']),
                rating=int(row['Rating'])
            )
            session.add(rating)
        
        # Import weather data
        try:
            df_weather = pd.read_csv("attached_assets/weather.csv")
            for _, row in df_weather.iterrows():
                # Check if a weather type already exists
                existing_weather = session.query(Weather).filter(Weather.weather_type == row['Weather_Type']).first()
                if not existing_weather:
                    weather = Weather(
                        weather_type=row['Weather_Type'],
                        preferred_foods=row['Preferred_Foods']
                    )
                    session.add(weather)
        except Exception as e:
            print(f"Error importing weather data: {e}")
        
        # Add a test user for easy login
        test_user = User(
            username="test",
            password="test",
            age="Adult",
            gender="Other",
            dietary_preference="Non-Vegetarian",
            allergies="None"
        )
        session.add(test_user)
        
        # Commit changes to the database
        session.commit()
        print("Data imported successfully")
    
    except Exception as e:
        session.rollback()
        print(f"Error importing data: {e}")
    finally:
        session.close()

def get_user_by_username(username):
    """Get a user by username"""
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).first()
        return user
    finally:
        session.close()

def get_user_preferences(user_id):
    """Get user preferences for all weather types"""
    session = Session()
    try:
        preferences = session.query(UserPreference).filter(UserPreference.user_id == user_id).all()
        return preferences
    finally:
        session.close()

def get_user_weather_preference(user_id, weather_type):
    """Get user preferences for a specific weather type"""
    session = Session()
    try:
        preference = session.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.weather_type == weather_type
        ).first()
        return preference
    finally:
        session.close()

def get_liked_disliked_foods(user_id):
    """Get a user's liked and disliked foods"""
    session = Session()
    try:
        liked_disliked = session.query(LikedDislikedFood).filter(
            LikedDislikedFood.user_id == user_id
        ).all()
        
        liked_foods = [item.food_id for item in liked_disliked if item.status == 'liked']
        disliked_foods = [item.food_id for item in liked_disliked if item.status == 'disliked']
        
        return liked_foods, disliked_foods
    finally:
        session.close()

def add_liked_disliked_food(user_id, food_id, status):
    """Add a food to a user's liked or disliked list"""
    session = Session()
    try:
        # Check if food is already in liked/disliked list
        existing = session.query(LikedDislikedFood).filter(
            LikedDislikedFood.user_id == user_id,
            LikedDislikedFood.food_id == food_id
        ).first()
        
        if existing:
            # Update status if it exists
            existing.status = status
        else:
            # Add new entry if it doesn't exist
            new_entry = LikedDislikedFood(
                user_id=user_id,
                food_id=food_id,
                status=status
            )
            session.add(new_entry)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error adding liked/disliked food: {e}")
        return False
    finally:
        session.close()

def get_search_history(user_id):
    """Get a user's search history"""
    session = Session()
    try:
        history = session.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).order_by(SearchHistory.timestamp.desc()).all()
        
        return [item.search_term for item in history]
    finally:
        session.close()

def add_search_term(user_id, search_term):
    """Add a search term to a user's search history"""
    session = Session()
    try:
        search = SearchHistory(
            user_id=user_id,
            search_term=search_term,
            timestamp=time.time()
        )
        session.add(search)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error adding search term: {e}")
        return False
    finally:
        session.close()

def get_food_by_id(food_id):
    """Get a food by ID"""
    session = Session()
    try:
        food = session.query(Food).filter(Food.id == food_id).first()
        return food
    finally:
        session.close()

def get_foods_by_ids(food_ids):
    """Get multiple foods by ID"""
    session = Session()
    try:
        foods = session.query(Food).filter(Food.id.in_(food_ids)).all()
        return foods
    finally:
        session.close()

def search_foods(query):
    """Search for foods based on a query string"""
    session = Session()
    try:
        # Search in dish name, cuisine type, and description
        foods = session.query(Food).filter(
            (Food.dish_name.ilike(f"%{query}%")) |
            (Food.cuisine_type.ilike(f"%{query}%")) |
            (Food.description.ilike(f"%{query}%"))
        ).all()
        
        return foods
    finally:
        session.close()

def get_weather_foods(weather_type):
    """Get preferred foods for a specific weather type"""
    session = Session()
    try:
        weather = session.query(Weather).filter(Weather.weather_type == weather_type).first()
        if weather and weather.preferred_foods:
            return weather.preferred_foods.split(', ')
        return []
    finally:
        session.close()

def create_user(username, password, age, gender, dietary_preference, allergies, weather_preferences):
    """Create a new user with preferences"""
    session = Session()
    try:
        # Check if username already exists
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            return None
        
        # Create new user
        new_user = User(
            username=username,
            password=password,  # In a real app, this would be hashed
            age=age,
            gender=gender,
            dietary_preference=dietary_preference,
            allergies=allergies
        )
        session.add(new_user)
        session.flush()  # Get the ID of the new user
        
        # Add user preferences for each weather type
        for weather_type, prefs in weather_preferences.items():
            user_pref = UserPreference(
                user_id=new_user.id,
                weather_type=weather_type,
                spice_preference=prefs['spice'],
                sugar_preference=prefs['sugar'],
                meal_type=prefs['meal_type']
            )
            session.add(user_pref)
        
        session.commit()
        return new_user.id
    except Exception as e:
        session.rollback()
        print(f"Error creating user: {e}")
        return None
    finally:
        session.close()

def update_user_preference(user_id, weather_type, spice_pref, sugar_pref, meal_type):
    """Update a user's preferences for a specific weather type"""
    session = Session()
    try:
        # Check if preference exists
        pref = session.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.weather_type == weather_type
        ).first()
        
        if pref:
            # Update existing preference
            pref.spice_preference = spice_pref
            pref.sugar_preference = sugar_pref
            pref.meal_type = meal_type
        else:
            # Create new preference
            pref = UserPreference(
                user_id=user_id,
                weather_type=weather_type,
                spice_preference=spice_pref,
                sugar_preference=sugar_pref,
                meal_type=meal_type
            )
            session.add(pref)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error updating user preference: {e}")
        return False
    finally:
        session.close()

def get_all_foods():
    """Get all foods"""
    session = Session()
    try:
        foods = session.query(Food).all()
        return foods
    finally:
        session.close()

def convert_db_food_to_dict(food):
    """Convert a Food ORM object to a dictionary"""
    return {
        'Food_ID': food.id,
        'Dish_Name': food.dish_name,
        'Cuisine_Type': food.cuisine_type,
        'Veg_Non': food.veg_non,
        'Describe': food.description,
        'Spice_Level': food.spice_level,
        'Sugar_Level': food.sugar_level,
        'Dish_Category': food.dish_category,
        'Weather_Type': food.weather_type
    }

def convert_db_user_to_dict(user):
    """Convert a User ORM object to a dictionary"""
    return {
        'user_id': user.id,
        'username': user.username,
        'age': user.age,
        'gender': user.gender,
        'dietary_preference': user.dietary_preference,
        'allergies': user.allergies
    }