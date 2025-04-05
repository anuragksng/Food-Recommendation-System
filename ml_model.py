"""
Advanced machine learning models for food recommendation with strict dietary filtering.
"""
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from data_loader import load_data, get_food_details
from database.db_operations import (get_user_by_username, convert_db_food_to_dict,
                                   get_user_preferences, search_foods, convert_db_user_to_dict)

def filter_by_dietary_preference(food_items, dietary_preference):
    """
    Filter food items based on dietary preference with strict validation
    
    Args:
        food_items: List of food item dictionaries
        dietary_preference: User's dietary preference
        
    Returns:
        list: Filtered food items
    """
    if not food_items:
        return []
        
    if not dietary_preference or dietary_preference.lower() == 'none':
        return food_items
        
    filtered_items = []
    
    # Normalize the dietary preference
    dp_lower = dietary_preference.lower()
    
    for item in food_items:
        # Skip items without Veg_Non information for strict filtering
        if 'Veg_Non' not in item or item['Veg_Non'] is None:
            # Only include for non-vegetarian users
            if dp_lower not in ['vegetarian', 'vegan']:
                filtered_items.append(item)
            continue
            
        # Normalize the Veg_Non value
        veg_status = str(item['Veg_Non']).lower() if item['Veg_Non'] else ""
        
        # For vegetarians, only include vegetarian items
        if dp_lower == 'vegetarian':
            if veg_status == 'veg' or veg_status == 'vegetarian':
                filtered_items.append(item)
                
        # For vegans, only include vegan items 
        elif dp_lower == 'vegan':
            if veg_status == 'vegan':
                filtered_items.append(item)
                
        # For gluten-free, exclude items with gluten
        elif dp_lower == 'gluten-free':
            # This is simplified - in a real app, would need more detailed data
            item_desc = str(item.get('Describe', '')).lower()
            if 'gluten' not in item_desc or 'gluten-free' in item_desc:
                filtered_items.append(item)
                
        # For non-vegetarians, include all items
        else:
            filtered_items.append(item)
            
    return filtered_items

def create_cuisine_preference_model(user_id, liked_foods):
    """
    Create a machine learning model to determine cuisine preferences from liked foods
    
    Args:
        user_id: User ID
        liked_foods: List of food IDs that the user has liked
        
    Returns:
        dict: Cuisine preference scores
    """
    if not liked_foods:
        return {}
        
    # Load data
    _, df_food, _, _, _ = load_data()
    
    # Get details of liked foods
    liked_food_details = []
    for food_id in liked_foods:
        food = get_food_details(food_id)
        if food:
            liked_food_details.append(food)
    
    if not liked_food_details:
        return {}
    
    # Count cuisine preferences
    cuisine_counts = {}
    for food in liked_food_details:
        cuisine = food.get('Cuisine_Type', 'Unknown')
        if cuisine and cuisine != 'Unknown':
            cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
    
    # Calculate preference scores (normalized)
    total = sum(cuisine_counts.values())
    cuisine_preferences = {cuisine: count/total for cuisine, count in cuisine_counts.items()}
    
    return cuisine_preferences

def generate_content_based_recommendations(user_id, dietary_preference, weather_type, limit=20):
    """
    Generate content-based recommendations using TF-IDF and cosine similarity
    
    Args:
        user_id: User ID
        dietary_preference: User's dietary preference
        weather_type: Current weather
        limit: Maximum number of recommendations
        
    Returns:
        list: Recommended food items
    """
    # Load data
    _, df_food, _, _, _ = load_data()
    
    # Create a copy to avoid warnings
    df_food = df_food.copy()
    
    # First, strict filter based on weather type
    weather_foods = df_food[df_food['Weather_Type'] == weather_type].copy()
    if weather_foods.empty:
        weather_foods = df_food  # Fallback to all foods if none match weather
    
    # Convert columns to appropriate types
    weather_foods.loc[:, 'Food_ID'] = pd.to_numeric(weather_foods['Food_ID'], errors='coerce').fillna(0).astype(int)
    weather_foods.loc[:, 'Spice_Level'] = pd.to_numeric(weather_foods['Spice_Level'], errors='coerce').fillna(0).astype(int)
    weather_foods.loc[:, 'Sugar_Level'] = pd.to_numeric(weather_foods['Sugar_Level'], errors='coerce').fillna(0).astype(int)
    
    # Create feature matrix from food descriptions and attributes
    weather_foods['features'] = (
        weather_foods['Dish_Name'].fillna('') + ' ' + 
        weather_foods['Cuisine_Type'].fillna('') + ' ' + 
        weather_foods['Dish_Category'].fillna('') + ' ' +
        weather_foods['Describe'].fillna('')
    )
    
    # Create TF-IDF vectorizer
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(weather_foods['features'])
    
    # Create K-nearest neighbors model
    model = NearestNeighbors(n_neighbors=min(limit, len(weather_foods)), 
                            metric='cosine', algorithm='brute')
    model.fit(tfidf_matrix)
    
    # Get liked foods to use as a reference point
    liked_foods, _ = get_liked_disliked_from_db(user_id)
    
    # If user has liked foods, use the average feature vector as query point
    if liked_foods:
        liked_indices = []
        for food_id in liked_foods:
            idx = weather_foods.index[weather_foods['Food_ID'] == food_id].tolist()
            if idx:
                liked_indices.extend(idx)
        
        if liked_indices:
            query_vector = tfidf_matrix[liked_indices].mean(axis=0)
            distances, indices = model.kneighbors(query_vector)
            recommended_indices = indices[0]
        else:
            # If no liked foods match weather foods, use random sampling
            recommended_indices = np.random.choice(
                len(weather_foods), size=min(limit, len(weather_foods)), replace=False)
    else:
        # If no liked foods, use random sampling
        recommended_indices = np.random.choice(
            len(weather_foods), size=min(limit, len(weather_foods)), replace=False)
    
    # Convert recommendations to list of dictionaries
    recommendations = []
    for idx in recommended_indices:
        row = weather_foods.iloc[idx]
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
    
    # Filter recommendations by dietary preference
    filtered_recommendations = filter_by_dietary_preference(recommendations, dietary_preference)
    
    # Return the remaining recommendations (or all if none were filtered)
    return filtered_recommendations[:limit]

def get_liked_disliked_from_db(user_id):
    """Helper function to get liked and disliked foods from database"""
    from database.db_operations import get_liked_disliked_foods
    return get_liked_disliked_foods(user_id)

def hybrid_recommendations(user_id, weather_type, limit=10):
    """
    Generate hybrid recommendations combining content-based and collaborative filtering
    with strict dietary preference filtering
    
    Args:
        user_id: User ID
        weather_type: Current weather
        limit: Maximum number of recommendations
        
    Returns:
        list: Recommended food items
    """
    # Get user information including dietary preference
    user = get_user_by_username_by_id(user_id)
    if not user:
        return []
    
    dietary_preference = user.get('dietary_preference', 'Non-Vegetarian')
    
    # Get liked and disliked foods
    liked_foods, disliked_foods = get_liked_disliked_from_db(user_id)
    
    # Generate content-based recommendations
    content_recs = generate_content_based_recommendations(
        user_id, dietary_preference, weather_type, limit=limit*2)
    
    # Get collaborative recommendations
    collab_recs = collaborative_filtering_recommendations(
        user_id, liked_foods, disliked_foods, limit=limit*2)
    
    # Filter recommendations by dietary preference
    content_recs = filter_by_dietary_preference(content_recs, dietary_preference)
    collab_recs = filter_by_dietary_preference(collab_recs, dietary_preference)
    
    # Combine recommendations with a weight (70% content-based, 30% collaborative)
    # and remove duplicates
    all_recs = []
    seen_food_ids = set()
    
    # Add content-based first (higher priority)
    for rec in content_recs:
        if rec['Food_ID'] not in seen_food_ids:
            seen_food_ids.add(rec['Food_ID'])
            all_recs.append(rec)
            
    # Add collaborative next
    for rec in collab_recs:
        if rec['Food_ID'] not in seen_food_ids:
            seen_food_ids.add(rec['Food_ID'])
            all_recs.append(rec)
    
    # Return limited results
    return all_recs[:limit]

def get_user_by_username_by_id(user_id):
    """Helper function to get user by ID"""
    from database.db_operations import get_user_by_username
    
    # Since our function expects username, we need a workaround
    # This is simplified - in a real app, would have a proper get_user_by_id function
    session = None
    try:
        from database.db_config import get_session_factory
        Session = get_session_factory()
        session = Session()
        
        from database.models import User
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            return convert_db_user_to_dict(user)
        return None
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None
    finally:
        if session:
            session.close()

def collaborative_filtering_recommendations(user_id, liked_foods, disliked_foods, limit=10):
    """Generate recommendations using collaborative filtering"""
    # Load data
    _, df_food, _, _, df_ratings = load_data()
    
    # If no ratings or liked foods, return empty list
    if df_ratings.empty or not liked_foods:
        return []
    
    # Create user-item matrix
    user_item_matrix = df_ratings.pivot_table(
        index='User_ID', columns='Food_ID', values='Rating', fill_value=0)
    
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
    for food_id in list(recommended_food_ids)[:limit]:
        food_item = get_food_details(food_id)
        if food_item:
            recommendations.append(food_item)
    
    return recommendations