import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from data_loader import load_data, get_food_details
from database.db_operations import (get_food_by_id, get_foods_by_ids, 
                                  get_user_weather_preference, search_foods,
                                  get_weather_foods, get_liked_disliked_foods, convert_db_food_to_dict,
                                  get_user_by_username)
from ml_model import (filter_by_dietary_preference, hybrid_recommendations,
                    generate_content_based_recommendations, get_user_by_username_by_id,
                    is_food_compatible_with_preference)

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
    # Get user information to determine dietary preference
    user_info = get_user_by_username_by_id(user_id)
    
    if not user_info:
        # Fallback to original implementation if user info not available
        return legacy_generate_recommendations(user_id, weather_preference, user_preferences)
        
    # Get dietary preference
    dietary_preference = user_info.get('dietary_preference', 'Non-Vegetarian')
    
    try:
        # Use the hybrid recommendation model for more accurate, personalized results
        recommendations = hybrid_recommendations(user_id, weather_preference, limit=10)
    except Exception as e:
        # If hybrid recommendations fail, start with an empty list
        recommendations = []
    
    # If we don't have enough recommendations, fall back to content-based filtering
    if len(recommendations) < 5:
        try:
            content_based_recs = generate_content_based_recommendations(
                user_id, dietary_preference, weather_preference, limit=10)
            
            # Combine recommendations, removing duplicates
            seen_food_ids = {int(r['Food_ID']) for r in recommendations}
            for rec in content_based_recs:
                rec_id = int(rec['Food_ID']) if isinstance(rec['Food_ID'], (int, float, str)) else 0
                if rec_id not in seen_food_ids:
                    recommendations.append(rec)
                    seen_food_ids.add(rec_id)
        except Exception as e:
            # Continue with what we have if content-based fails
            pass
            
        # Stop once we have enough recommendations
        if len(recommendations) >= 10:
            # Early exit if we already have enough recommendations
            return recommendations
    
    # Make sure the recommendations adhere to the user's dietary preferences
    recommendations = filter_by_dietary_preference(recommendations, dietary_preference)
    
    # If still not enough recommendations after filtering, use legacy method
    if len(recommendations) < 3:
        legacy_recs = legacy_generate_recommendations(user_id, weather_preference, user_preferences)
        # Filter the legacy recommendations too
        legacy_recs = filter_by_dietary_preference(legacy_recs, dietary_preference)
        
        # Add unique recommendations from legacy method
        seen_food_ids = {r['Food_ID'] for r in recommendations}
        for rec in legacy_recs:
            if rec['Food_ID'] not in seen_food_ids:
                recommendations.append(rec)
                seen_food_ids.add(rec['Food_ID'])
                
                # Stop once we have enough recommendations
                if len(recommendations) >= 10:
                    break
    
    return recommendations

def legacy_generate_recommendations(user_id, weather_preference, user_preferences=None):
    """
    Original recommendation algorithm as a fallback method
    
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
        
        # Convert preference values to integers to avoid type mismatch
        spice_pref_int = int(spice_pref) if spice_pref is not None else 5
        sugar_pref_int = int(sugar_pref) if sugar_pref is not None else 5
        
        # Now calculate differences
        weather_foods.loc[:, 'spice_diff'] = abs(weather_foods['Spice_Level'] - spice_pref_int)
        weather_foods.loc[:, 'sugar_diff'] = abs(weather_foods['Sugar_Level'] - sugar_pref_int)
        
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
    # Get user information to determine dietary preference
    user_info = get_user_by_username_by_id(user_id)
    if not user_info:
        # Fall back to legacy method if user info not available
        return legacy_update_recommendations(user_id, weather_preference, liked_foods, disliked_foods, search_history)
    
    # Get dietary preference
    dietary_preference = user_info.get('dietary_preference', 'Non-Vegetarian')
    
    # Use advanced hybrid recommendations
    recommendations = hybrid_recommendations(user_id, weather_preference, limit=15)
    
    # Add content-based recommendations from search history (if any)
    if search_history:
        # Get content-based recommendations from search history
        content_recs = []
        for search_term in search_history[:3]:  # Use recent searches
            foods = search_foods(search_term)
            for food in foods:
                content_recs.append(convert_db_food_to_dict(food))
        
        # Remove duplicates
        seen_food_ids = {rec['Food_ID'] for rec in recommendations}
        for rec in content_recs:
            if rec['Food_ID'] not in seen_food_ids:
                recommendations.append(rec)
                seen_food_ids.add(rec['Food_ID'])
    
    # Filter recommendations by dietary preference
    filtered_recommendations = filter_by_dietary_preference(recommendations, dietary_preference)
    
    # If not enough recommendations, use the legacy method as a fallback
    if len(filtered_recommendations) < 5:
        legacy_recs = legacy_update_recommendations(user_id, weather_preference, liked_foods, disliked_foods, search_history)
        legacy_filtered = filter_by_dietary_preference(legacy_recs, dietary_preference)
        
        # Add unique items from legacy recommendations
        seen_food_ids = {rec['Food_ID'] for rec in filtered_recommendations}
        for rec in legacy_filtered:
            if rec['Food_ID'] not in seen_food_ids:
                filtered_recommendations.append(rec)
                seen_food_ids.add(rec['Food_ID'])
                
                # Stop once we have enough recommendations
                if len(filtered_recommendations) >= 10:
                    break
    
    # Return up to 10 recommendations
    return filtered_recommendations[:10]

def legacy_update_recommendations(user_id, weather_preference, liked_foods, disliked_foods, search_history):
    """
    Original recommendation update algorithm as a fallback method
    
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
    initial_recs = legacy_generate_recommendations(user_id, weather_preference)
    
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

def search_food(query, df_food=None, user_id=None):
    """
    Search for food items based on a query string and user's dietary preference
    with strict dietary preference filtering
    
    Args:
        query: Search query
        df_food: Food dataframe (if already loaded)
        user_id: The ID of the user (for dietary preference filtering)
        
    Returns:
        list: Matching food items
    """
    # If query is empty, return empty results
    if not query or query.strip() == "":
        return []
    
    # Get user's dietary preference if user_id is provided
    dietary_preference = None
    if user_id:
        user_info = get_user_by_username_by_id(user_id)
        if user_info:
            dietary_preference = user_info.get('dietary_preference')
    
    print(f"User dietary preference: {dietary_preference}")  # Debug log
    
    # Search in database first
    db_results = search_foods(query)
    if db_results:
        results = [convert_db_food_to_dict(food) for food in db_results]
        
        # Apply strict dietary preference filtering if available
        if dietary_preference:
            # DOUBLE-CHECK: First use the new helper function
            filtered_results = []
            for item in results:
                if is_food_compatible_with_preference(item, dietary_preference):
                    filtered_results.append(item)
                    
            # Then also apply the main filter function as a backup
            filtered_results = filter_by_dietary_preference(filtered_results, dietary_preference)
            
            # Log filtering results
            print(f"Search filtered foods from {len(results)} to {len(filtered_results)} based on {dietary_preference} preference")
            
            return filtered_results
        return results
    
    # If not in database or no results, search in dataframe
    if df_food is None:
        df_user, df_food, df_weather, df_user_preferences, df_ratings = load_data()
    
    # Apply pre-filtering for dietary preference BEFORE search if applicable
    if dietary_preference and dietary_preference.lower() in ['vegetarian', 'vegan']:
        # Pre-filter the dataframe based on dietary preferences
        # This ensures we don't even search in non-matching foods
        vegStatus = ['veg', 'vegetarian'] if dietary_preference.lower() == 'vegetarian' else ['vegan']
        
        # Create a copy to avoid warnings
        df_food_filtered = df_food.copy()
        
        # Perform case-insensitive filtering
        mask = df_food_filtered['Veg_Non'].str.lower().isin(vegStatus)
        df_food_filtered = df_food_filtered[mask]
        
        # If we have results after filtering, use this dataframe instead
        if not df_food_filtered.empty:
            df_food = df_food_filtered
            print(f"Pre-filtered food dataframe to {len(df_food)} foods matching {dietary_preference}")
    
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
    
    # If no results, try more aggressive searching with words
    if search_results.empty and " " in query:
        print(f"No direct results for '{query}', trying word-level search")
        words = query.strip().split()
        for word in words:
            if len(word) > 2:  # Only use words longer than 2 characters
                word_mask = (
                    df_food['Dish_Name'].str.contains(word, case=False, na=False) |
                    df_food['Cuisine_Type'].str.contains(word, case=False, na=False) |
                    df_food['Dish_Category'].str.contains(word, case=False, na=False)
                )
                
                # Add description search if not empty
                if df_food['Describe'].notna().any():
                    word_mask = word_mask | df_food['Describe'].str.contains(word, case=False, na=False)
                
                word_results = df_food[word_mask]
                
                if not word_results.empty:
                    search_results = pd.concat([search_results, word_results])
    
    # If still no results, return empty list
    if search_results.empty:
        return []
    
    # Ensure numeric columns are properly converted
    search_results.loc[:, 'Food_ID'] = pd.to_numeric(search_results['Food_ID'], errors='coerce').fillna(0).astype(int)
    search_results.loc[:, 'Spice_Level'] = pd.to_numeric(search_results['Spice_Level'], errors='coerce').fillna(0).astype(int)
    search_results.loc[:, 'Sugar_Level'] = pd.to_numeric(search_results['Sugar_Level'], errors='coerce').fillna(0).astype(int)
    
    # Remove duplicates based on Food_ID
    search_results = search_results.drop_duplicates(subset=['Food_ID'])
    
    # Convert to list of dictionaries
    results = []
    for _, row in search_results.iterrows():
        food_item = {
            'Food_ID': int(row['Food_ID']),
            'Dish_Name': row['Dish_Name'],
            'Cuisine_Type': row['Cuisine_Type'],
            'Veg_Non': row['Veg_Non'] if not pd.isna(row['Veg_Non']) else "",
            'Describe': row['Describe'] if not pd.isna(row['Describe']) else "No description available",
            'Spice_Level': int(row['Spice_Level']),
            'Sugar_Level': int(row['Sugar_Level']),
            'Dish_Category': row['Dish_Category'],
            'Weather_Type': row['Weather_Type']
        }
        results.append(food_item)
    
    # Apply final dietary preference filtering
    if dietary_preference:
        # DOUBLE-CHECK: First use the individual item checker
        filtered_results = []
        for item in results:
            if is_food_compatible_with_preference(item, dietary_preference):
                filtered_results.append(item)
                
        # Then also apply the main filter function as a backup
        filtered_results = filter_by_dietary_preference(filtered_results, dietary_preference)
        
        # Log filtering results
        print(f"CSV search filtered foods from {len(results)} to {len(filtered_results)} based on {dietary_preference} preference")
        
        return filtered_results
        
    return results