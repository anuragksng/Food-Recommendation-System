import streamlit as st
import pandas as pd
import numpy as np
import os

@st.cache_data
def load_data():
    """
    Load and preprocess all required datasets
    
    Returns:
        Tuple of dataframes: (df_user, df_food, df_weather, df_user_preferences, df_ratings)
    """
    # Define file paths
    user_csv = "attached_assets/user.csv"
    food_csv = "attached_assets/food.csv"
    weather_csv = "attached_assets/weather.csv"
    user_preferences_csv = "attached_assets/user_preferences.csv"
    ratings_csv = "attached_assets/ratings.csv"
    
    # Load the datasets
    df_user = pd.read_csv(user_csv)
    df_food = pd.read_csv(food_csv)
    df_weather = pd.read_csv(weather_csv)
    df_user_preferences = pd.read_csv(user_preferences_csv)
    df_ratings = pd.read_csv(ratings_csv)
    
    # Clean and preprocess the data
    
    # Handle missing values in food descriptions
    df_food['Describe'] = df_food['Describe'].fillna('No description available.')
    
    # Convert string representations to appropriate data types where needed
    df_food['Spice_Level'] = pd.to_numeric(df_food['Spice_Level'], errors='coerce').fillna(0).astype(int)
    df_food['Sugar_Level'] = pd.to_numeric(df_food['Sugar_Level'], errors='coerce').fillna(0).astype(int)
    
    # Ensure all Food_ID fields are integers
    df_food['Food_ID'] = df_food['Food_ID'].astype(int)
    # Fill NaN values in the Food_ID column before converting to integer
    df_ratings['Food_ID'] = pd.to_numeric(df_ratings['Food_ID'], errors='coerce').fillna(0).astype(int)
    
    # Ensure all User_ID fields are integers
    df_user['User_ID'] = df_user['User_ID'].astype(int)
    df_user_preferences['User_ID'] = df_user_preferences['User_ID'].astype(int)
    # Fill NaN values in the User_ID column before converting to integer
    df_ratings['User_ID'] = pd.to_numeric(df_ratings['User_ID'], errors='coerce').fillna(0).astype(int)
    
    # Ensure Rating column is also handled properly
    df_ratings['Rating'] = pd.to_numeric(df_ratings['Rating'], errors='coerce').fillna(0).astype(int)
    
    # Clean allergies data (replace NaN with "None")
    df_user['Allergies'] = df_user['Allergies'].fillna('None')
    
    # Parse the preferred foods in weather dataset
    df_weather['Preferred_Foods'] = df_weather['Preferred_Foods'].str.split(', ')
    
    return df_user, df_food, df_weather, df_user_preferences, df_ratings

def get_food_details(food_id):
    """
    Get details of a specific food item by ID
    
    Args:
        food_id: The ID of the food item
        
    Returns:
        dict: Food item details
    """
    _, df_food, _, _, _ = load_data()
    
    food_item = df_food[df_food['Food_ID'] == food_id]
    
    if food_item.empty:
        return None
    
    return food_item.iloc[0].to_dict()

def get_user_preferences(user_id):
    """
    Get the preferences of a specific user by ID
    
    Args:
        user_id: The ID of the user
        
    Returns:
        dict: User preferences
    """
    df_user, _, _, df_user_preferences, _ = load_data()
    
    user_info = df_user[df_user['User_ID'] == user_id]
    user_prefs = df_user_preferences[df_user_preferences['User_ID'] == user_id]
    
    if user_info.empty:
        return None
    
    # Compile user preferences
    preferences = {
        'dietary': user_info.iloc[0]['Dietary_Preferences'],
        'age': user_info.iloc[0]['Age'],
        'gender': user_info.iloc[0]['Gender'],
        'allergies': user_info.iloc[0]['Allergies'],
        'weather_preferences': {}
    }
    
    # Add weather-specific preferences
    for _, row in user_prefs.iterrows():
        preferences['weather_preferences'][row['Weather_Type']] = {
            'spice': row['Spice_Preference'],
            'sugar': row['Sugar_Preference'],
            'meal_type': row['Meal_Type']
        }
    
    return preferences

def get_user_ratings(user_id):
    """
    Get the ratings given by a specific user
    
    Args:
        user_id: The ID of the user
        
    Returns:
        DataFrame: User ratings
    """
    _, _, _, _, df_ratings = load_data()
    
    user_ratings = df_ratings[df_ratings['User_ID'] == user_id]
    
    return user_ratings
