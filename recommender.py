import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from data_loader import load_data, get_food_details, get_user_preferences, get_user_ratings

def generate_initial_recommendations(user_id, weather_preference, user_preferences=None):
    """
    Generate initial food recommendations for a user based on their preferences and current weather
    
    Args:
        user_id: The ID of the user
        weather_preference: Current weather condition
        user_preferences: User's preferences (if already loaded)
        
    Returns:
        list: List of recommended food items
    """
    # Load the required data
    df_user, df_food, df_weather, df_user_preferences, df_ratings = load_data()
    
    # Get user preferences if not provided
    if user_preferences is None:
        user_preferences = get_user_preferences(user_id)
    
    # Get weather-based preferred foods
    weather_foods = df_weather[df_weather['Weather_Type'] == weather_preference]['Preferred_Foods'].iloc[0]
    if isinstance(weather_foods, str):
        weather_foods = weather_foods.split(', ')
    
    # Get user's weather-specific preferences
    weather_prefs = {}
    if weather_preference in user_preferences.get('weather_preferences', {}):
        weather_prefs = user_preferences['weather_preferences'][weather_preference]
    
    # Get user's dietary preferences
    dietary_pref = user_preferences.get('dietary', 'Non-Vegetarian')
    
    # Get user's allergies
    allergies = user_preferences.get('allergies', 'None')
    if isinstance(allergies, str):
        allergies = [allergy.strip() for allergy in allergies.split(',')]
    
    # Filter food items based on dietary preferences
    if dietary_pref == 'Vegetarian':
        filtered_foods = df_food[df_food['Veg_Non'] == 'Vegetarian']
    elif dietary_pref == 'Vegan':
        filtered_foods = df_food[df_food['Veg_Non'] == 'Vegetarian']  # Assuming vegan items are a subset of vegetarian
    else:
        filtered_foods = df_food.copy()
    
    # Score each food item based on user preferences
    food_scores = []
    
    for _, food in filtered_foods.iterrows():
        score = 0
        
        # Increase score for foods that match weather preference
        if any(food_name.lower() in food['Dish_Name'].lower() for food_name in weather_foods):
            score += 10
        
        # Match spice level preference
        if 'spice' in weather_prefs:
            spice_diff = abs(food['Spice_Level'] - weather_prefs['spice'])
            score -= spice_diff  # Penalize based on how far from preferred spice level
        
        # Match sugar level preference
        if 'sugar' in weather_prefs:
            sugar_diff = abs(food['Sugar_Level'] - weather_prefs['sugar'])
            score -= sugar_diff  # Penalize based on how far from preferred sugar level
        
        # Handle allergies - significant penalty for allergens
        if allergies and allergies != 'None':
            for allergen in allergies:
                if allergen.strip() != 'None' and allergen.strip().lower() in food['Dish_Name'].lower():
                    score -= 100  # Heavy penalty for allergens
        
        food_scores.append({
            'food_id': food['Food_ID'],
            'score': score,
            'food_item': food.to_dict()
        })
    
    # Sort foods by score
    sorted_foods = sorted(food_scores, key=lambda x: x['score'], reverse=True)
    
    # Take top 20 recommendations
    top_recommendations = [item['food_item'] for item in sorted_foods[:20]]
    
    return top_recommendations

def update_recommendations(user_id, weather_preference, liked_foods, disliked_foods, search_history):
    """
    Update food recommendations based on user feedback and search history
    
    Args:
        user_id: The ID of the user
        weather_preference: Current weather condition
        liked_foods: List of food IDs that the user has liked
        disliked_foods: List of food IDs that the user has disliked
        search_history: List of search terms used by the user
        
    Returns:
        list: Updated list of recommended food items
    """
    # Load the required data
    df_user, df_food, df_weather, df_user_preferences, df_ratings = load_data()
    
    # Get user preferences
    user_preferences = get_user_preferences(user_id)
    
    # Get initial recommendations
    initial_recommendations = generate_initial_recommendations(user_id, weather_preference, user_preferences)
    
    # Calculate a collaborative filtering component if there are enough liked foods
    collaborative_recommendations = []
    if len(liked_foods) > 0:
        collaborative_recommendations = collaborative_filtering(user_id, liked_foods, disliked_foods)
    
    # Calculate a content-based component based on search history
    content_recommendations = []
    if len(search_history) > 0:
        content_recommendations = content_based_filtering(search_history, liked_foods, disliked_foods)
    
    # Combine the recommendation strategies
    # Start with the initial recommendations as the base
    combined_recommendations = initial_recommendations.copy()
    
    # Add collaborative and content-based recommendations, avoiding duplicates
    all_food_ids = [food['Food_ID'] for food in combined_recommendations]
    
    # Add collaborative recommendations
    for food in collaborative_recommendations:
        if food['Food_ID'] not in all_food_ids and food['Food_ID'] not in disliked_foods:
            combined_recommendations.append(food)
            all_food_ids.append(food['Food_ID'])
    
    # Add content-based recommendations
    for food in content_recommendations:
        if food['Food_ID'] not in all_food_ids and food['Food_ID'] not in disliked_foods:
            combined_recommendations.append(food)
            all_food_ids.append(food['Food_ID'])
    
    # Ensure we don't recommend disliked foods
    filtered_recommendations = [food for food in combined_recommendations if food['Food_ID'] not in disliked_foods]
    
    # Prioritize recommendations based on liked foods
    # Move liked foods to the top of the list
    for food_id in liked_foods:
        for i, food in enumerate(filtered_recommendations):
            if food['Food_ID'] == food_id:
                # Move to the front
                filtered_recommendations.pop(i)
                filtered_recommendations.insert(0, food)
                break
    
    return filtered_recommendations

def collaborative_filtering(user_id, liked_foods, disliked_foods):
    """
    Generate recommendations using collaborative filtering based on user's food preferences
    
    Args:
        user_id: The ID of the user
        liked_foods: List of food IDs that the user has liked
        disliked_foods: List of food IDs that the user has disliked
        
    Returns:
        list: Recommended food items from collaborative filtering
    """
    # Load the required data
    df_user, df_food, _, _, df_ratings = load_data()
    
    # If no ratings data or not enough liked foods, return empty list
    if df_ratings.empty or len(liked_foods) == 0:
        return []
    
    # Create a user-item matrix
    user_item_matrix = df_ratings.pivot_table(
        index='User_ID', 
        columns='Food_ID', 
        values='Rating', 
        fill_value=0
    )
    
    # Create a similarity matrix based on user ratings
    user_similarities = cosine_similarity(user_item_matrix)
    
    # Convert to DataFrame for easier manipulation
    user_similarities_df = pd.DataFrame(
        user_similarities, 
        index=user_item_matrix.index, 
        columns=user_item_matrix.index
    )
    
    # Check if user_id is in the matrix
    if user_id not in user_similarities_df.index:
        # User is not in the ratings data, use a different approach
        # For simplicity, we'll just return popular items
        popular_foods = df_ratings.groupby('Food_ID')['Rating'].mean().sort_values(ascending=False).index.tolist()
        popular_food_items = [df_food[df_food['Food_ID'] == food_id].iloc[0].to_dict() for food_id in popular_foods[:10]
                             if food_id not in disliked_foods]
        return popular_food_items
    
    # Get similar users to the current user
    similar_users = user_similarities_df[user_id].sort_values(ascending=False).index[1:6]  # top 5 similar users, excluding self
    
    # Get recommendations from similar users
    recommended_foods = set()
    for similar_user in similar_users:
        # Get foods that similar user rated highly
        similar_user_ratings = df_ratings[(df_ratings['User_ID'] == similar_user) & (df_ratings['Rating'] > 6)]
        for _, row in similar_user_ratings.iterrows():
            if row['Food_ID'] not in liked_foods and row['Food_ID'] not in disliked_foods:
                recommended_foods.add(row['Food_ID'])
    
    # Get details of recommended foods
    recommended_food_items = []
    for food_id in recommended_foods:
        food_item = df_food[df_food['Food_ID'] == food_id]
        if not food_item.empty:
            recommended_food_items.append(food_item.iloc[0].to_dict())
    
    return recommended_food_items

def content_based_filtering(search_history, liked_foods, disliked_foods):
    """
    Generate recommendations based on user's search history
    
    Args:
        search_history: List of search terms used by the user
        liked_foods: List of food IDs that the user has liked
        disliked_foods: List of food IDs that the user has disliked
        
    Returns:
        list: Recommended food items from content-based filtering
    """
    # Load the required data
    _, df_food, _, _, _ = load_data()
    
    # If no search history, return empty list
    if not search_history:
        return []
    
    # Score each food based on search terms
    food_scores = []
    
    for _, food in df_food.iterrows():
        # Skip if already liked or disliked
        if food['Food_ID'] in liked_foods or food['Food_ID'] in disliked_foods:
            continue
        
        score = 0
        
        # Check for matches in the food name, cuisine, and description
        for term in search_history:
            term = term.lower()
            if term in food['Dish_Name'].lower():
                score += 10
            if term in food['Cuisine_Type'].lower():
                score += 5
            if term in str(food['Describe']).lower():
                score += 3
        
        if score > 0:
            food_scores.append({
                'food_id': food['Food_ID'],
                'score': score,
                'food_item': food.to_dict()
            })
    
    # Sort by score and get top recommendations
    sorted_foods = sorted(food_scores, key=lambda x: x['score'], reverse=True)
    top_recommendations = [item['food_item'] for item in sorted_foods[:10]]
    
    return top_recommendations

def search_food(query, df_food=None):
    """
    Search for food items based on a query string
    
    Args:
        query: Search query
        df_food: Food dataframe (if already loaded)
        
    Returns:
        list: Matching food items
    """
    # Load food data if not provided
    if df_food is None:
        _, df_food, _, _, _ = load_data()
    
    # Convert query to lowercase for case-insensitive matching
    query = query.lower()
    
    # Search in dish name, cuisine type, and description
    matches = df_food[
        df_food['Dish_Name'].str.lower().str.contains(query) |
        df_food['Cuisine_Type'].str.lower().str.contains(query) |
        df_food['Describe'].str.lower().str.contains(query)
    ]
    
    # Convert the matches to a list of dictionaries for easy use
    results = [row.to_dict() for _, row in matches.iterrows()]
    
    return results
