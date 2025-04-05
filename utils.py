import streamlit as st
import pandas as pd
import numpy as np
import random

def display_food_item(food_item, index):
    """
    Display a food item in a card layout
    
    Args:
        food_item: Dictionary containing food item details
        index: Index of the food item for unique keys
    """
    st.write(f"### {food_item['Dish_Name']}")
    
    # Show basic food information
    st.write(f"**Cuisine:** {food_item['Cuisine_Type']}")
    st.write(f"**Type:** {food_item['Veg_Non']}")
    
    # Display spice and sugar levels with progress bars
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Spice Level:**")
        st.progress(food_item['Spice_Level'] / 10)
    
    with col2:
        st.write("**Sugar Level:**")
        st.progress(food_item['Sugar_Level'] / 10)
    
    # Like/Dislike buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"👍 Like", key=f"like_{index}_{food_item['Food_ID']}"):
            if food_item['Food_ID'] not in st.session_state.liked_foods:
                st.session_state.liked_foods.append(food_item['Food_ID'])
                if food_item['Food_ID'] in st.session_state.disliked_foods:
                    st.session_state.disliked_foods.remove(food_item['Food_ID'])
                # Update recommendations
                from recommender import update_recommendations
                st.session_state.personalized_recommendations = update_recommendations(
                    st.session_state.user_id,
                    st.session_state.weather_preference,
                    st.session_state.liked_foods,
                    st.session_state.disliked_foods,
                    st.session_state.search_history
                )
                st.success(f"You liked {food_item['Dish_Name']}!")
                st.rerun()
    
    with col2:
        if st.button(f"👎 Dislike", key=f"dislike_{index}_{food_item['Food_ID']}"):
            if food_item['Food_ID'] not in st.session_state.disliked_foods:
                st.session_state.disliked_foods.append(food_item['Food_ID'])
                if food_item['Food_ID'] in st.session_state.liked_foods:
                    st.session_state.liked_foods.remove(food_item['Food_ID'])
                # Update recommendations
                from recommender import update_recommendations
                st.session_state.personalized_recommendations = update_recommendations(
                    st.session_state.user_id,
                    st.session_state.weather_preference,
                    st.session_state.liked_foods,
                    st.session_state.disliked_foods,
                    st.session_state.search_history
                )
                st.error(f"You disliked {food_item['Dish_Name']}!")
                st.rerun()
    
    # View details button
    if st.button(f"View Details", key=f"details_{index}_{food_item['Food_ID']}"):
        st.session_state.selected_food = food_item
        display_food_details(food_item)
    
    st.markdown("---")

def display_food_details(food_item):
    """
    Display detailed information for a food item
    
    Args:
        food_item: Dictionary containing food item details
    """
    st.write(f"## {food_item['Dish_Name']}")
    
    # Basic information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Cuisine:** {food_item['Cuisine_Type']}")
        st.write(f"**Category:** {food_item['Dish_Category']}")
        st.write(f"**Type:** {food_item['Veg_Non']}")
        st.write(f"**Ideal Weather:** {food_item['Weather_Type']}")
    
    with col2:
        # Display spice and sugar levels with progress bars
        st.write("**Spice Level:**")
        st.progress(food_item['Spice_Level'] / 10)
        
        st.write("**Sugar Level:**")
        st.progress(food_item['Sugar_Level'] / 10)
    
    # Description
    st.write("### Description")
    # Clean up HTML tags from description
    description = food_item['Describe']
    description = description.replace('<b>', '**').replace('</b>', '**')
    description = description.replace('...[Truncated]', '...')
    st.write(description)
    
    # Like/Dislike buttons
    col1, col2 = st.columns(2)
    
    with col1:
        liked = food_item['Food_ID'] in st.session_state.liked_foods
        button_text = "👍 Liked" if liked else "👍 Like"
        
        if st.button(button_text, key=f"detail_like_{food_item['Food_ID']}"):
            if not liked:
                st.session_state.liked_foods.append(food_item['Food_ID'])
                if food_item['Food_ID'] in st.session_state.disliked_foods:
                    st.session_state.disliked_foods.remove(food_item['Food_ID'])
                # Update recommendations
                from recommender import update_recommendations
                st.session_state.personalized_recommendations = update_recommendations(
                    st.session_state.user_id,
                    st.session_state.weather_preference,
                    st.session_state.liked_foods,
                    st.session_state.disliked_foods,
                    st.session_state.search_history
                )
                st.success(f"You liked {food_item['Dish_Name']}!")
                st.rerun()
    
    with col2:
        disliked = food_item['Food_ID'] in st.session_state.disliked_foods
        button_text = "👎 Disliked" if disliked else "👎 Dislike"
        
        if st.button(button_text, key=f"detail_dislike_{food_item['Food_ID']}"):
            if not disliked:
                st.session_state.disliked_foods.append(food_item['Food_ID'])
                if food_item['Food_ID'] in st.session_state.liked_foods:
                    st.session_state.liked_foods.remove(food_item['Food_ID'])
                # Update recommendations
                from recommender import update_recommendations
                st.session_state.personalized_recommendations = update_recommendations(
                    st.session_state.user_id,
                    st.session_state.weather_preference,
                    st.session_state.liked_foods,
                    st.session_state.disliked_foods,
                    st.session_state.search_history
                )
                st.error(f"You disliked {food_item['Dish_Name']}!")
                st.rerun()
    
    st.markdown("---")

def get_user_name(user_id):
    """
    Get the username for a given user ID
    
    Args:
        user_id: The ID of the user
        
    Returns:
        str: The username (or default if not found)
    """
    # In a real app, this would query a user database
    # For this demo, we'll use a convention of "User {ID}"
    return f"User {user_id}"

def format_allergies(allergies_str):
    """
    Format allergies string for display
    
    Args:
        allergies_str: String containing allergies
        
    Returns:
        str: Formatted allergies string
    """
    if not allergies_str or allergies_str == 'None':
        return "None"
    
    # Split by comma and remove empty strings
    allergies = [allergy.strip() for allergy in allergies_str.split(',') if allergy.strip()]
    
    # Remove 'None' entries if other allergies are present
    if len(allergies) > 1 and 'None' in allergies:
        allergies.remove('None')
    
    return ", ".join(allergies)
