import streamlit as st
import pandas as pd
import random
from datetime import datetime
from auth import login, signup, check_authentication
from data_loader import load_data, get_food_details, get_user_preferences_dict
from recommender import generate_initial_recommendations, update_recommendations, search_food, legacy_generate_recommendations, legacy_update_recommendations
from utils import display_food_item, display_food_details, format_allergies
from database.db_operations import (get_user_by_username, add_liked_disliked_food,
                                  get_liked_disliked_foods, add_search_term,
                                  get_search_history, convert_db_user_to_dict)

# Set page config
st.set_page_config(
    page_title="Food Recommendation System",
    page_icon="🍽️",
    layout="wide"
)

# Initialize session state variables
if 'weather' not in st.session_state:
    st.session_state['weather'] = None  # Will be set after user login
    
if 'viewing_food' not in st.session_state:
    st.session_state['viewing_food'] = None
    
if 'recommendations' not in st.session_state:
    st.session_state['recommendations'] = []
    
if 'search_query' not in st.session_state:
    st.session_state['search_query'] = ''
    
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = []

def main():
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 0.25rem 0.5rem rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
    .weather-select {
        width: 100%;
        padding: 0.5rem;
        border-radius: 0.25rem;
        border: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display header
    st.markdown('<div class="main-header">Food Recommendation System</div>', unsafe_allow_html=True)
    
    # Check if user is logged in
    if not check_authentication():
        # Show login/signup options
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            login()
            
        with tab2:
            signup()
            
    else:
        # If a user is logged in, show the main app
        show_main_app()

def show_main_app():
    # Get user information
    user_id = st.session_state['user_id']
    username = st.session_state['username']
    
    # Display welcome message and user info
    user = get_user_by_username(username)
    
    if user:
        # Convert to dictionary for easier access
        user_dict = convert_db_user_to_dict(user)
        
        # Show user profile in sidebar
        with st.sidebar:
            st.markdown(f"# Welcome, {username}!")
            st.markdown("### Your Profile")
            st.markdown(f"**Age Group:** {user_dict['age']}")
            st.markdown(f"**Dietary Preference:** {user_dict['dietary_preference']}")
            st.markdown(f"**Allergies:** {format_allergies(user_dict['allergies'])}")
            
            # Display current weather preference (read-only)
            st.markdown("### Current Weather")
            st.markdown(f"**Weather Type:** {st.session_state['weather']}")
            st.markdown("*Weather preferences are set during signup and\nused for your personalized recommendations.*")
            
            # Logout button
            if st.button("Logout"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    # Main content area
    if st.session_state['viewing_food'] is not None:
        # Show detailed view of a food item
        food_item = get_food_details(st.session_state['viewing_food'])
        if food_item:
            back_button = display_food_details(food_item)
            if back_button:
                st.session_state['viewing_food'] = None
                st.rerun()
    else:
        # Show search and recommendations
        col1, col2 = st.columns(2)
        
        # Search column
        with col1:
            st.markdown('<div class="sub-header">Search for Food</div>', unsafe_allow_html=True)
            
            search_query = st.text_input("Enter food name, cuisine, or keywords:",
                                       value=st.session_state['search_query'])
            
            if search_query != st.session_state['search_query']:
                st.session_state['search_query'] = search_query
                if search_query:
                    # Add to search history
                    add_search_term(user_id, search_query)
                    # Get search results with dietary preference filtering
                    st.session_state['search_results'] = search_food(search_query, user_id=user_id)
                else:
                    st.session_state['search_results'] = []
            
            if st.session_state['search_results']:
                st.markdown(f"Found {len(st.session_state['search_results'])} results:")
                
                for i, food_item in enumerate(st.session_state['search_results']):
                    action = display_food_item(food_item, f"search_{i}")
                    
                    if action == "like":
                        add_liked_disliked_food(user_id, food_item['Food_ID'], 'liked')
                        st.success(f"Added {food_item['Dish_Name']} to your liked foods!")
                        st.rerun()
                        
                    elif action == "dislike":
                        add_liked_disliked_food(user_id, food_item['Food_ID'], 'disliked')
                        st.success(f"Added {food_item['Dish_Name']} to your disliked foods!")
                        st.rerun()
                        
                    elif action == "details":
                        st.session_state['viewing_food'] = food_item['Food_ID']
                        st.rerun()
            elif search_query:
                st.warning("No results found. Try a different search term.")
        
        # Recommendations column
        with col2:
            st.markdown('<div class="sub-header">Recommendations for You</div>', unsafe_allow_html=True)
            
            # Weather info
            st.markdown(f"Based on **{st.session_state['weather']}** weather conditions")
            
            # We will load recommendations as needed in the section below
            
            # Force refresh recommendations button
            if st.button("Refresh Recommendations"):
                st.session_state['recommendations'] = []
                st.rerun()
            
            # Display recommendations
            if st.session_state['recommendations']:
                for i, food_item in enumerate(st.session_state['recommendations']):
                    action = display_food_item(food_item, f"rec_{i}")
                    
                    if action == "like":
                        add_liked_disliked_food(user_id, food_item['Food_ID'], 'liked')
                        st.success(f"Added {food_item['Dish_Name']} to your liked foods!")
                        st.session_state['recommendations'] = []
                        st.rerun()
                        
                    elif action == "dislike":
                        add_liked_disliked_food(user_id, food_item['Food_ID'], 'disliked')
                        st.success(f"Added {food_item['Dish_Name']} to your disliked foods!")
                        st.session_state['recommendations'] = []
                        st.rerun()
                        
                    elif action == "details":
                        st.session_state['viewing_food'] = food_item['Food_ID']
                        st.rerun()
            else:
                # Show loading message
                with st.spinner("Generating your personalized recommendations..."):
                    try:
                        # Check if weather is set, if not use a default
                        if st.session_state['weather'] is None:
                            st.session_state['weather'] = 'Cold'
                            st.warning("Using default 'Cold' weather for recommendations.")
                        
                        # Get liked and disliked foods
                        liked_foods, disliked_foods = get_liked_disliked_foods(user_id)
                        
                        # Get search history
                        search_history = get_search_history(user_id)
                        
                        # Get user's dietary preference for filtering
                        user_dict = convert_db_user_to_dict(user)
                        dietary_preference = user_dict.get('dietary_preference', 'NonVegetarian')
                        
                        # Use the legacy generation method but apply strict filtering
                        recommendations = legacy_generate_recommendations(
                            user_id, 
                            st.session_state['weather']
                        )
                        
                        # Import the strict filtering functions
                        from strict_filter import apply_strict_filtering
                        from ml_model import filter_by_dietary_preference
                        
                        # Apply dietary preference filtering
                        recommendations = filter_by_dietary_preference(recommendations, dietary_preference)
                        
                        # Apply strict filtering to ensure only compatible food types are shown
                        st.session_state['recommendations'] = apply_strict_filtering(recommendations, dietary_preference)
                        
                        print(f"App.py: After strict filtering, {len(st.session_state['recommendations'])} recommendations for {dietary_preference} user")
                        
                        # If we got recommendations, and the user has preferences, enhance with user data
                        if st.session_state['recommendations'] and (liked_foods or search_history):
                            # Try to enhance recommendations with user preferences
                            try:
                                enhanced_recs = update_recommendations(
                                    user_id, 
                                    st.session_state['weather'],
                                    liked_foods, 
                                    disliked_foods, 
                                    search_history
                                )
                                if enhanced_recs:
                                    st.session_state['recommendations'] = enhanced_recs
                            except Exception as e:
                                st.warning(f"Could not enhance recommendations with your preferences.")
                    except Exception as e:
                        st.error(f"Error generating recommendations: {e}")
                        # Use empty list if all fails
                        st.session_state['recommendations'] = []
                
                # If still no recommendations after trying to generate them, show a message
                if not st.session_state['recommendations']:
                    # Try one more time with a fallback approach
                    try:
                        # Last attempt with minimal dependencies
                        df_user, df_food, df_weather, df_user_preferences, df_ratings = load_data()
                        # Just grab some random food items as a last resort
                        # Get user's dietary preference for filtering
                        user_dict = convert_db_user_to_dict(user)
                        dietary_preference = user_dict.get('dietary_preference', 'NonVegetarian')
                        
                        # Filter food dataframe by Type based on dietary preference
                        if 'Type' in df_food.columns:
                            if dietary_preference == 'Vegetarian':
                                sample_foods = df_food[df_food['Type'] == 'Vegetarian'].sample(min(20, len(df_food)))
                            else:
                                sample_foods = df_food[df_food['Type'] == 'NonVegetarian'].sample(min(20, len(df_food)))
                        elif 'Veg_Non' in df_food.columns:
                            if dietary_preference == 'Vegetarian':
                                sample_foods = df_food[df_food['Veg_Non'] == 'Vegetarian'].sample(min(20, len(df_food)))
                            else:
                                sample_foods = df_food[df_food['Veg_Non'] == 'Non-Vegetarian'].sample(min(20, len(df_food)))
                        else:
                            # If no type column, get random samples and filter later
                            sample_foods = df_food.sample(min(20, len(df_food)))
                            
                        recommendations = []
                        for _, row in sample_foods.iterrows():
                            food_item = {
                                'Food_ID': int(row['Food_ID']) if pd.notna(row['Food_ID']) else 0,
                                'Dish_Name': row['Dish_Name'] if pd.notna(row['Dish_Name']) else "Unknown",
                                'Cuisine_Type': row['Cuisine_Type'] if pd.notna(row['Cuisine_Type']) else "Various",
                                'Veg_Non': row['Veg_Non'] if pd.notna(row['Veg_Non']) else "Non-veg",
                                'Describe': row['Describe'] if pd.notna(row['Describe']) else "No description available",
                                'Spice_Level': int(row['Spice_Level']) if pd.notna(row['Spice_Level']) else 5,
                                'Sugar_Level': int(row['Sugar_Level']) if pd.notna(row['Sugar_Level']) else 5,
                                'Dish_Category': row['Dish_Category'] if pd.notna(row['Dish_Category']) else "Main",
                                'Weather_Type': row['Weather_Type'] if pd.notna(row['Weather_Type']) else "Any"
                            }
                            
                            # Add Type column if present
                            if 'Type' in row and not pd.isna(row['Type']):
                                food_item['Type'] = row['Type']
                            elif 'Veg_Non' in row and not pd.isna(row['Veg_Non']):
                                # Standardize to Type
                                veg_status = str(row['Veg_Non']).lower()
                                food_item['Type'] = 'NonVegetarian' if 'non' in veg_status else 'Vegetarian'
                            
                            recommendations.append(food_item)
                            
                        # Apply dietary preference filtering to be extra sure
                        from strict_filter import apply_strict_filtering
                        from ml_model import filter_by_dietary_preference
                        
                        recommendations = filter_by_dietary_preference(recommendations, dietary_preference)
                        st.session_state['recommendations'] = apply_strict_filtering(recommendations, dietary_preference)
                        
                        print(f"App.py fallback: After strict filtering, {len(st.session_state['recommendations'])} recommendations for {dietary_preference} user")
                    except Exception as e:
                        st.error("Unable to generate any recommendations. Please try refreshing the page.")
                
                # Force a rerun to display the new recommendations if we have any
                if st.session_state['recommendations']:
                    st.rerun()

# Create necessary Streamlit config files
import os
if not os.path.exists(".streamlit"):
    os.makedirs(".streamlit")
    
if not os.path.exists(".streamlit/config.toml"):
    with open(".streamlit/config.toml", "w") as f:
        f.write("""
[server]
headless = true
address = "0.0.0.0"
port = 5000
""")

# Load initial data
if __name__ == "__main__":
    # Pre-load the data
    load_data()
    # Run the app
    main()