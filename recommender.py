import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from data_loader import load_data, get_food_details
from database.db_operations import (get_food_by_id, get_foods_by_ids, 
                                  get_user_weather_preference, search_foods,
                                  get_weather_foods, get_liked_disliked_foods, convert_db_food_to_dict)

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
    # Load data
    df_user, df_food, df_weather, df_user_preferences, df_ratings = load_data()
    
    # Get preferred foods for current weather from weather table
    weather_preferred_foods = get_weather_foods(weather_preference)
    
    # Get liked and disliked foods
    liked_foods, disliked_foods = get_liked_disliked_foods(user_id)
    
    # Filter foods based on weather
    weather_foods = df_food[df_food['Weather_Type'] == weather_preference]
    
    # Get user preferences for current weather
    user_pref = get_user_weather_preference(user_id, weather_preference)
    
    if user_pref:
        # Filter foods based on preferences
        spice_pref = user_pref.spice_preference
        sugar_pref = user_pref.sugar_preference
        meal_type = user_pref.meal_type
        
        # Calculate similarity scores - ensure proper type conversion
        # Create a copy to avoid SettingWithCopyWarning
        weather_foods = weather_foods.copy()
        
        # First make sure spice and sugar levels are numeric
        weather_foods.loc[:, 'Spice_Level'] = pd.to_numeric(weather_foods['Spice_Level'], errors='coerce').fillna(0).astype(int)
        weather_foods.loc[:, 'Sugar_Level'] = pd.to_numeric(weather_foods['Sugar_Level'], errors='coerce').fillna(0).astype(int)
        
        # Now calculate differences
        weather_foods.loc[:, 'spice_diff'] = abs(weather_foods['Spice_Level'] - spice_pref)
        weather_foods.loc[:, 'sugar_diff'] = abs(weather_foods['Sugar_Level'] - sugar_pref)
        
        # Weighted score (lower is better)
        weather_foods.loc[:, 'score'] = weather_foods['spice_diff'] + weather_foods['sugar_diff']
        
        # Filter by meal type if specified
        if meal_type and meal_type.lower() != 'any':
            # First make sure Dish_Category is properly handled for missing values
            weather_foods.loc[:, 'Dish_Category'] = weather_foods['Dish_Category'].fillna('').astype(str)
            
            # Create meal filter that handles NaN values properly
            meal_filter = weather_foods['Dish_Category'].str.lower().str.contains(meal_type.lower(), na=False)
            
            # Apply filter only if we have valid results
            if meal_filter.any():
                weather_foods = weather_foods[meal_filter]
        
        # Sort by score (ascending)
        weather_foods = weather_foods.sort_values('score')
    
    # Remove disliked foods
    if disliked_foods and not weather_foods.empty:
        # Make sure Food_ID is properly formatted first
        weather_foods = weather_foods.copy()  # Create a copy to avoid SettingWithCopyWarning
        weather_foods.loc[:, 'Food_ID'] = pd.to_numeric(weather_foods['Food_ID'], errors='coerce').fillna(0).astype(int)
        
        # Convert disliked_foods to integers for proper comparison
        disliked_foods_int = [int(x) for x in disliked_foods if pd.notna(x)]
        
        if disliked_foods_int:
            weather_foods = weather_foods[~weather_foods['Food_ID'].isin(disliked_foods_int)]
    
    # Convert to list of dictionaries
    recommendations = []
    for _, row in weather_foods.head(10).iterrows():
        food_item = {
            'Food_ID': int(row['Food_ID']),
            'Dish_Name': row['Dish_Name'],
            'Cuisine_Type': row['Cuisine_Type'],
            'Veg_Non': row['Veg_Non'],
            'Describe': row['Describe'] if not pd.isna(row['Describe']) else "No description available",
            'Spice_Level': int(row['Spice_Level']),
            'Sugar_Level': int(row['Sugar_Level']),
            'Dish_Category': row['Dish_Category'],
            'Weather_Type': row['Weather_Type']
        }
        recommendations.append(food_item)
    
    # If we don't have enough recommendations, add general recommendations
    if len(recommendations) < 5:
        # Add some general recommendations from foods table
        general_recs = df_food.sample(min(5, len(df_food)))
        
        # Create a copy to avoid SettingWithCopyWarning
        general_recs = general_recs.copy()
        
        # Ensure numeric columns are properly converted
        general_recs.loc[:, 'Food_ID'] = pd.to_numeric(general_recs['Food_ID'], errors='coerce').fillna(0).astype(int)
        general_recs.loc[:, 'Spice_Level'] = pd.to_numeric(general_recs['Spice_Level'], errors='coerce').fillna(0).astype(int)
        general_recs.loc[:, 'Sugar_Level'] = pd.to_numeric(general_recs['Sugar_Level'], errors='coerce').fillna(0).astype(int)
        
        for _, row in general_recs.iterrows():
            if int(row['Food_ID']) not in [r['Food_ID'] for r in recommendations]:
                food_item = {
                    'Food_ID': int(row['Food_ID']),
                    'Dish_Name': row['Dish_Name'],
                    'Cuisine_Type': row['Cuisine_Type'],
                    'Veg_Non': row['Veg_Non'],
                    'Describe': row['Describe'] if not pd.isna(row['Describe']) else "No description available",
                    'Spice_Level': int(row['Spice_Level']),
                    'Sugar_Level': int(row['Sugar_Level']),
                    'Dish_Category': row['Dish_Category'],
                    'Weather_Type': row['Weather_Type']
                }
                recommendations.append(food_item)
    
    return recommendations

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
    # Get initial recommendations
    initial_recs = generate_initial_recommendations(user_id, weather_preference)
    
    # Get collaborative and content-based recommendations
    collab_recs = []
    
    if liked_foods:
        collab_recs = collaborative_filtering(user_id, liked_foods, disliked_foods)
    
    content_recs = []
    if search_history:
        content_recs = content_based_filtering(search_history, liked_foods, disliked_foods)
    
    # Combine recommendations, prioritizing collaborative and content-based ones
    all_recs = collab_recs + content_recs
    
    # Remove duplicates by keeping track of food IDs
    seen_food_ids = set()
    unique_recs = []
    
    for rec in all_recs:
        if rec['Food_ID'] not in seen_food_ids:
            seen_food_ids.add(rec['Food_ID'])
            unique_recs.append(rec)
    
    # Add initial recommendations to fill out the list
    for rec in initial_recs:
        if len(unique_recs) >= 10:
            break
            
        if rec['Food_ID'] not in seen_food_ids:
            seen_food_ids.add(rec['Food_ID'])
            unique_recs.append(rec)
    
    return unique_recs

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
    # Load data
    df_user, df_food, df_weather, df_user_preferences, df_ratings = load_data()
    
    # If no ratings or liked foods, return empty list
    if df_ratings.empty or not liked_foods:
        return []
    
    # Create user-item matrix
    user_item_matrix = df_ratings.pivot_table(index='User_ID', columns='Food_ID', values='Rating', fill_value=0)
    
    # Create a profile for the current user based on their liked and disliked foods
    user_profile = pd.Series(0, index=user_item_matrix.columns)
    
    # Assign ratings of 5 for liked foods and 1 for disliked foods
    for food_id in liked_foods:
        if food_id in user_profile.index:
            user_profile[food_id] = 5
            
    for food_id in disliked_foods:
        if food_id in user_profile.index:
            user_profile[food_id] = 1
    
    # Calculate similarity between the current user and all other users
    similarities = []
    for user in user_item_matrix.index:
        if user != user_id:
            # Calculate similarity (cosine) between the two users
            user_vector = user_item_matrix.loc[user].values.reshape(1, -1)
            profile_vector = user_profile.values.reshape(1, -1)
            
            # Handle zero vectors
            if np.sum(user_vector) > 0 and np.sum(profile_vector) > 0:
                sim = cosine_similarity(user_vector, profile_vector)[0][0]
                similarities.append((user, sim))
    
    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Get top similar users
    similar_users = [user for user, sim in similarities[:5] if sim > 0]
    
    # Get food IDs highly rated by similar users
    recommended_food_ids = set()
    for user in similar_users:
        user_ratings = df_ratings[df_ratings['User_ID'] == user]
        highly_rated = user_ratings[user_ratings['Rating'] >= 4]['Food_ID'].tolist()
        recommended_food_ids.update(highly_rated)
    
    # Remove foods that the current user has already rated
    # First, convert liked_foods and disliked_foods to integers
    liked_foods_int = [int(x) for x in liked_foods if str(x).isdigit()]
    disliked_foods_int = [int(x) for x in disliked_foods if str(x).isdigit()]
    
    # Then create a set with valid food IDs only
    rated_foods = set(liked_foods_int + disliked_foods_int)
    
    # Remove rated foods from recommendations
    recommended_food_ids = recommended_food_ids - rated_foods
    
    # Get details for the recommended foods
    recommendations = []
    for food_id in list(recommended_food_ids)[:5]:
        food_item = get_food_details(food_id)
        if food_item:
            recommendations.append(food_item)
    
    return recommendations

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
    if not search_history:
        return []
    
    # Take the most recent search terms
    recent_searches = search_history[:3]
    
    # Search for foods based on search terms
    search_results = []
    for search_term in recent_searches:
        foods = search_foods(search_term)
        for food in foods:
            # Convert to dict format
            search_results.append(convert_db_food_to_dict(food))
    
    # Remove duplicates and already rated items
    seen_food_ids = set()
    filtered_results = []
    
    # Convert liked_foods and disliked_foods to integers for proper comparison
    liked_foods_int = [int(x) for x in liked_foods if str(x).isdigit()]
    disliked_foods_int = [int(x) for x in disliked_foods if str(x).isdigit()]
    
    for food in search_results:
        food_id = int(food['Food_ID'])  # Ensure food_id is an integer
        if (food_id not in seen_food_ids and 
            food_id not in liked_foods_int and 
            food_id not in disliked_foods_int):
            seen_food_ids.add(food_id)
            filtered_results.append(food)
    
    return filtered_results[:5]

def search_food(query, df_food=None):
    """
    Search for food items based on a query string
    
    Args:
        query: Search query
        df_food: Food dataframe (if already loaded)
        
    Returns:
        list: Matching food items
    """
    # Search in database first
    db_results = search_foods(query)
    if db_results:
        return [convert_db_food_to_dict(food) for food in db_results]
    
    # If not in database or no results, search in dataframe
    if df_food is None:
        df_user, df_food, df_weather, df_user_preferences, df_ratings = load_data()
    
    # Search in dish name, cuisine type, and description
    mask = (
        df_food['Dish_Name'].str.contains(query, case=False, na=False) |
        df_food['Cuisine_Type'].str.contains(query, case=False, na=False) |
        df_food['Dish_Category'].str.contains(query, case=False, na=False)
    )
    
    # Add description search if not empty
    if df_food['Describe'].notna().any():
        mask = mask | df_food['Describe'].str.contains(query, case=False, na=False)
    
    search_results = df_food[mask]
    
    # Create a copy to avoid SettingWithCopyWarning
    search_results = search_results.copy()
    
    # Ensure numeric columns are properly converted
    search_results.loc[:, 'Food_ID'] = pd.to_numeric(search_results['Food_ID'], errors='coerce').fillna(0).astype(int)
    search_results.loc[:, 'Spice_Level'] = pd.to_numeric(search_results['Spice_Level'], errors='coerce').fillna(0).astype(int)
    search_results.loc[:, 'Sugar_Level'] = pd.to_numeric(search_results['Sugar_Level'], errors='coerce').fillna(0).astype(int)
    
    # Convert to list of dictionaries
    results = []
    for _, row in search_results.iterrows():
        food_item = {
            'Food_ID': int(row['Food_ID']),
            'Dish_Name': row['Dish_Name'],
            'Cuisine_Type': row['Cuisine_Type'],
            'Veg_Non': row['Veg_Non'],
            'Describe': row['Describe'] if not pd.isna(row['Describe']) else "No description available",
            'Spice_Level': int(row['Spice_Level']),
            'Sugar_Level': int(row['Sugar_Level']),
            'Dish_Category': row['Dish_Category'],
            'Weather_Type': row['Weather_Type']
        }
        results.append(food_item)
    
    return results