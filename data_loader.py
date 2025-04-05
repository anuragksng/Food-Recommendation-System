import os
import pandas as pd
import streamlit as st
from database.db_operations import (get_food_by_id, get_foods_by_ids, convert_db_food_to_dict,
                                   get_user_preferences, get_user_by_username, init_db,
                                   import_initial_data)

@st.cache_data
def load_data():
    """
    Load and preprocess all required datasets
    
    Returns:
        Tuple of dataframes: (df_user, df_food, df_weather, df_user_preferences, df_ratings)
    """
    # Initialize the database and import data if needed
    init_db()
    import_initial_data()
    
    # Load user data
    df_user = pd.read_csv("attached_assets/user.csv")
    
    # Load food data
    df_food = pd.read_csv("attached_assets/food.csv")
    
    # Load weather data
    df_weather = pd.read_csv("attached_assets/weather.csv")
    
    # Load user preferences
    df_user_preferences = pd.read_csv("attached_assets/user_preferences.csv")
    
    # Load ratings data
    df_ratings = pd.read_csv("attached_assets/ratings.csv")
    
    # Clean and preprocess data to avoid NaN conversion errors
    
    # Drop rows with NaN in critical columns
    df_ratings = df_ratings.dropna(subset=['User_ID', 'Food_ID', 'Rating'])
    
    # Convert IDs and numeric columns to integers safely using pd.to_numeric with proper error handling
    
    # For ratings dataframe
    df_ratings['User_ID'] = pd.to_numeric(df_ratings['User_ID'], errors='coerce').fillna(0).astype(int)
    df_ratings['Food_ID'] = pd.to_numeric(df_ratings['Food_ID'], errors='coerce').fillna(0).astype(int)
    df_ratings['Rating'] = pd.to_numeric(df_ratings['Rating'], errors='coerce').fillna(0).astype(int)
    
    # For user dataframe
    df_user['User_ID'] = pd.to_numeric(df_user['User_ID'], errors='coerce').fillna(0).astype(int)
    
    # For food dataframe
    df_food['Food_ID'] = pd.to_numeric(df_food['Food_ID'], errors='coerce').fillna(0).astype(int)
    df_food['Spice_Level'] = pd.to_numeric(df_food['Spice_Level'], errors='coerce').fillna(0).astype(int)
    df_food['Sugar_Level'] = pd.to_numeric(df_food['Sugar_Level'], errors='coerce').fillna(0).astype(int)
    
    # For user preferences dataframe
    df_user_preferences['User_ID'] = pd.to_numeric(df_user_preferences['User_ID'], errors='coerce').fillna(0).astype(int)
    if 'Spice_Preference' in df_user_preferences.columns:
        df_user_preferences['Spice_Preference'] = pd.to_numeric(df_user_preferences['Spice_Preference'], errors='coerce').fillna(0).astype(int)
    if 'Sugar_Preference' in df_user_preferences.columns:
        df_user_preferences['Sugar_Preference'] = pd.to_numeric(df_user_preferences['Sugar_Preference'], errors='coerce').fillna(0).astype(int)
    
    return df_user, df_food, df_weather, df_user_preferences, df_ratings

def get_food_details(food_id):
    """
    Get details of a specific food item by ID
    
    Args:
        food_id: The ID of the food item
        
    Returns:
        dict: Food item details
    """
    # First try to get from database
    food = get_food_by_id(food_id)
    if food:
        return convert_db_food_to_dict(food)
    
    # If not in database, get from dataframe
    df_user, df_food, df_weather, df_user_preferences, df_ratings = load_data()
    
    # Ensure numeric columns are properly converted
    df_food['Food_ID'] = pd.to_numeric(df_food['Food_ID'], errors='coerce').fillna(0).astype(int)
    df_food['Spice_Level'] = pd.to_numeric(df_food['Spice_Level'], errors='coerce').fillna(0).astype(int)
    df_food['Sugar_Level'] = pd.to_numeric(df_food['Sugar_Level'], errors='coerce').fillna(0).astype(int)
    
    food_row = df_food[df_food['Food_ID'] == food_id]
    
    if not food_row.empty:
        food_row = food_row.iloc[0]
        return {
            'Food_ID': int(food_row['Food_ID']),
            'Dish_Name': food_row['Dish_Name'],
            'Cuisine_Type': food_row['Cuisine_Type'],
            'Veg_Non': food_row['Veg_Non'],
            'Describe': food_row['Describe'] if not pd.isna(food_row['Describe']) else "No description available",
            'Spice_Level': int(food_row['Spice_Level']),
            'Sugar_Level': int(food_row['Sugar_Level']),
            'Dish_Category': food_row['Dish_Category'],
            'Weather_Type': food_row['Weather_Type']
        }
    
    return None

def get_user_preferences_dict(user_id):
    """
    Get the preferences of a specific user by ID
    
    Args:
        user_id: The ID of the user
        
    Returns:
        dict: User preferences
    """
    # Try to get from database
    preferences = get_user_preferences(user_id)
    if preferences:
        # Convert to dict format
        prefs_dict = {}
        for pref in preferences:
            prefs_dict[pref.weather_type] = {
                'spice': pref.spice_preference,
                'sugar': pref.sugar_preference,
                'meal_type': pref.meal_type
            }
        return prefs_dict
    
    # If not in database, get from dataframe
    df_user, df_food, df_weather, df_user_preferences, df_ratings = load_data()
    
    # Ensure columns are properly converted to correct types
    df_user_preferences['User_ID'] = pd.to_numeric(df_user_preferences['User_ID'], errors='coerce').fillna(0).astype(int)
    if 'Spice_Preference' in df_user_preferences.columns:
        df_user_preferences['Spice_Preference'] = pd.to_numeric(df_user_preferences['Spice_Preference'], errors='coerce').fillna(0).astype(int)
    if 'Sugar_Preference' in df_user_preferences.columns:
        df_user_preferences['Sugar_Preference'] = pd.to_numeric(df_user_preferences['Sugar_Preference'], errors='coerce').fillna(0).astype(int)
    
    user_prefs = df_user_preferences[df_user_preferences['User_ID'] == user_id]
    
    prefs_dict = {}
    for _, row in user_prefs.iterrows():
        prefs_dict[row['Weather_Type']] = {
            'spice': int(row['Spice_Preference']),
            'sugar': int(row['Sugar_Preference']),
            'meal_type': row['Meal_Type']
        }
    
    return prefs_dict

def get_user_ratings(user_id):
    """
    Get the ratings given by a specific user
    
    Args:
        user_id: The ID of the user
        
    Returns:
        DataFrame: User ratings
    """
    df_user, df_food, df_weather, df_user_preferences, df_ratings = load_data()
    return df_ratings[df_ratings['User_ID'] == user_id]