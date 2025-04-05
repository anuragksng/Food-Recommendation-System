import streamlit as st
import pandas as pd
import numpy as np
from auth import login, signup, check_authentication
from data_loader import load_data
from recommender import (
    generate_initial_recommendations,
    update_recommendations,
    search_food
)
from utils import display_food_details, display_food_item

# Set page configuration
st.set_page_config(
    page_title="Food Recommendation System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'liked_foods' not in st.session_state:
    st.session_state.liked_foods = []
if 'disliked_foods' not in st.session_state:
    st.session_state.disliked_foods = []
if 'searched_foods' not in st.session_state:
    st.session_state.searched_foods = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'initial_recommendations' not in st.session_state:
    st.session_state.initial_recommendations = []
if 'personalized_recommendations' not in st.session_state:
    st.session_state.personalized_recommendations = []
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'weather_preference' not in st.session_state:
    st.session_state.weather_preference = 'Cold'
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'food_data' not in st.session_state:
    st.session_state.food_data = {}
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'page_size' not in st.session_state:
    st.session_state.page_size = 6
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

# Load data when the app starts
df_user, df_food, df_weather, df_user_preferences, df_ratings = load_data()

# Store the dataframes in the session state
if 'df_user' not in st.session_state:
    st.session_state.df_user = df_user
if 'df_food' not in st.session_state:
    st.session_state.df_food = df_food
if 'df_weather' not in st.session_state:
    st.session_state.df_weather = df_weather
if 'df_user_preferences' not in st.session_state:
    st.session_state.df_user_preferences = df_user_preferences
if 'df_ratings' not in st.session_state:
    st.session_state.df_ratings = df_ratings

# Create sidebar for navigation
st.sidebar.title("Food Recommendation System")

# Authentication section
if not st.session_state.authenticated:
    st.sidebar.header("Authentication")
    auth_option = st.sidebar.radio("Choose an option:", ["Login", "Signup"])
    
    if auth_option == "Login":
        login()
    else:
        signup()
else:
    # User is authenticated, show navigation options
    st.sidebar.header(f"Welcome, {st.session_state.username}!")
    
    # Navigation options
    nav_option = st.sidebar.radio(
        "Navigation:",
        ["Home", "Recommendations", "Search", "Preferences", "Liked Foods", "Logout"]
    )
    
    # Handle navigation
    if nav_option == "Home":
        st.session_state.current_page = 'home'
    elif nav_option == "Recommendations":
        st.session_state.current_page = 'recommendations'
    elif nav_option == "Search":
        st.session_state.current_page = 'search'
    elif nav_option == "Preferences":
        st.session_state.current_page = 'preferences'
    elif nav_option == "Liked Foods":
        st.session_state.current_page = 'liked_foods'
    elif nav_option == "Logout":
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Reinitialize authenticated to False
        st.session_state.authenticated = False
        st.rerun()
    
    # Weather preference selection in sidebar
    st.sidebar.header("Current Weather")
    weather_options = ['Cold', 'Hot', 'Rainy', 'Humid', 'Windy']
    selected_weather = st.sidebar.selectbox(
        "Select current weather:", 
        weather_options,
        index=weather_options.index(st.session_state.weather_preference)
    )
    
    if selected_weather != st.session_state.weather_preference:
        st.session_state.weather_preference = selected_weather
        # Update recommendations based on new weather preference
        if hasattr(st.session_state, 'user_id') and st.session_state.user_id is not None:
            st.session_state.personalized_recommendations = update_recommendations(
                st.session_state.user_id,
                st.session_state.weather_preference,
                st.session_state.liked_foods,
                st.session_state.disliked_foods,
                st.session_state.search_history
            )
        st.rerun()

# Main content based on the current page
if st.session_state.authenticated:
    if st.session_state.current_page == 'home':
        st.title("Welcome to Food Recommendation System")
        st.write(f"Current weather: {st.session_state.weather_preference}")
        
        # Display personalized recommendations
        st.header("Personalized Recommendations")
        if len(st.session_state.personalized_recommendations) == 0:
            # Generate initial recommendations if not available
            st.session_state.personalized_recommendations = generate_initial_recommendations(
                st.session_state.user_id,
                st.session_state.weather_preference,
                st.session_state.user_preferences
            )
        
        # Display recommendations in a grid layout
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]
        
        start_idx = st.session_state.current_index
        end_idx = min(start_idx + st.session_state.page_size, len(st.session_state.personalized_recommendations))
        
        food_idx = 0
        for i in range(start_idx, end_idx):
            if i < len(st.session_state.personalized_recommendations):
                col = cols[food_idx % 3]
                with col:
                    food_item = st.session_state.personalized_recommendations[i]
                    display_food_item(food_item, i)
                food_idx += 1
        
        # Pagination controls
        st.write("")
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.session_state.current_index > 0:
                if st.button("Previous"):
                    st.session_state.current_index = max(0, st.session_state.current_index - st.session_state.page_size)
                    st.rerun()
        
        with col4:
            if end_idx < len(st.session_state.personalized_recommendations):
                if st.button("Next"):
                    st.session_state.current_index = min(
                        st.session_state.current_index + st.session_state.page_size,
                        len(st.session_state.personalized_recommendations) - 1
                    )
                    st.rerun()
                    
    elif st.session_state.current_page == 'recommendations':
        st.title("Food Recommendations")
        st.write(f"Based on your preferences and current weather: {st.session_state.weather_preference}")
        
        # Generate recommendations if not available
        if len(st.session_state.personalized_recommendations) == 0:
            st.session_state.personalized_recommendations = generate_initial_recommendations(
                st.session_state.user_id,
                st.session_state.weather_preference,
                st.session_state.user_preferences
            )
        
        # Display recommendations in a grid layout
        col1, col2 = st.columns(2)
        cols = [col1, col2]
        
        start_idx = st.session_state.current_index
        end_idx = min(start_idx + st.session_state.page_size, len(st.session_state.personalized_recommendations))
        
        food_idx = 0
        for i in range(start_idx, end_idx):
            if i < len(st.session_state.personalized_recommendations):
                col = cols[food_idx % 2]
                with col:
                    food_item = st.session_state.personalized_recommendations[i]
                    display_food_details(food_item)
                food_idx += 1
        
        # Pagination controls
        st.write("")
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.session_state.current_index > 0:
                if st.button("Previous"):
                    st.session_state.current_index = max(0, st.session_state.current_index - st.session_state.page_size)
                    st.rerun()
        
        with col4:
            if end_idx < len(st.session_state.personalized_recommendations):
                if st.button("Next"):
                    st.session_state.current_index = min(
                        st.session_state.current_index + st.session_state.page_size,
                        len(st.session_state.personalized_recommendations) - 1
                    )
                    st.rerun()
        
    elif st.session_state.current_page == 'search':
        st.title("Search Food Items")
        
        # Search functionality
        search_query = st.text_input("Search for food items:")
        search_btn = st.button("Search")
        
        if search_query and search_btn:
            st.session_state.search_results = search_food(search_query, st.session_state.df_food)
            if search_query not in st.session_state.search_history:
                st.session_state.search_history.append(search_query)
            
            # Update recommendations based on search
            st.session_state.personalized_recommendations = update_recommendations(
                st.session_state.user_id,
                st.session_state.weather_preference,
                st.session_state.liked_foods,
                st.session_state.disliked_foods,
                st.session_state.search_history
            )
        
        # Display search results
        if len(st.session_state.search_results) > 0:
            st.subheader(f"Search results for '{search_query}'")
            for i, food_item in enumerate(st.session_state.search_results):
                st.write(f"### {food_item['Dish_Name']}")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Cuisine:** {food_item['Cuisine_Type']}")
                    st.write(f"**Category:** {food_item['Dish_Category']}")
                    st.write(f"**Type:** {food_item['Veg_Non']}")
                    st.write(f"**Spice Level:** {food_item['Spice_Level']}/10")
                    st.write(f"**Sugar Level:** {food_item['Sugar_Level']}/10")
                
                with col2:
                    # Like/Dislike buttons
                    if st.button(f"👍 Like", key=f"like_{i}_{food_item['Food_ID']}"):
                        if food_item['Food_ID'] not in st.session_state.liked_foods:
                            st.session_state.liked_foods.append(food_item['Food_ID'])
                            if food_item['Food_ID'] in st.session_state.disliked_foods:
                                st.session_state.disliked_foods.remove(food_item['Food_ID'])
                            # Update recommendations based on new like
                            st.session_state.personalized_recommendations = update_recommendations(
                                st.session_state.user_id,
                                st.session_state.weather_preference,
                                st.session_state.liked_foods,
                                st.session_state.disliked_foods,
                                st.session_state.search_history
                            )
                            st.success(f"You liked {food_item['Dish_Name']}!")
                            st.rerun()
                    
                    if st.button(f"👎 Dislike", key=f"dislike_{i}_{food_item['Food_ID']}"):
                        if food_item['Food_ID'] not in st.session_state.disliked_foods:
                            st.session_state.disliked_foods.append(food_item['Food_ID'])
                            if food_item['Food_ID'] in st.session_state.liked_foods:
                                st.session_state.liked_foods.remove(food_item['Food_ID'])
                            # Update recommendations based on new dislike
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
        else:
            if search_query and search_btn:
                st.info("No results found.")
        
    elif st.session_state.current_page == 'preferences':
        st.title("Your Preferences")
        
        # Display current preferences
        st.subheader("Current Preferences")
        user_info = df_user[df_user['User_ID'] == st.session_state.user_id].iloc[0]
        
        st.write(f"**Age Group:** {user_info['Age']}")
        st.write(f"**Gender:** {user_info['Gender']}")
        st.write(f"**Dietary Preference:** {user_info['Dietary_Preferences']}")
        st.write(f"**Allergies:** {user_info['Allergies']}")
        
        # User's weather-based preferences
        st.subheader("Weather-Based Preferences")
        user_prefs = df_user_preferences[df_user_preferences['User_ID'] == st.session_state.user_id]
        
        for _, row in user_prefs.iterrows():
            st.write(f"**Weather:** {row['Weather_Type']}")
            st.write(f"**Meal Type:** {row['Meal_Type']}")
            st.write(f"**Spice Preference:** {row['Spice_Preference']}/10")
            st.write(f"**Sugar Preference:** {row['Sugar_Preference']}/10")
            
            if not pd.isna(row['Recent_Dislikes']) and row['Recent_Dislikes'] != '':
                st.write(f"**Recent Dislikes:** {row['Recent_Dislikes']}")
            
            st.markdown("---")
        
        # Update preferences form
        st.subheader("Update Preferences")
        
        with st.form("update_preferences"):
            dietary_pref = st.selectbox(
                "Dietary Preference:", 
                ["Non-Vegetarian", "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Paleo"],
                index=["Non-Vegetarian", "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Paleo"].index(user_info['Dietary_Preferences'])
            )
            
            # Allow updating of spice and sugar preferences for different weather conditions
            weather_type = st.selectbox("Weather Type:", ['Cold', 'Hot', 'Rainy', 'Humid', 'Windy'])
            
            # Get current preferences for selected weather
            current_pref = user_prefs[user_prefs['Weather_Type'] == weather_type]
            current_spice = 5
            current_sugar = 5
            
            if not current_pref.empty:
                current_spice = current_pref.iloc[0]['Spice_Preference']
                current_sugar = current_pref.iloc[0]['Sugar_Preference']
            
            spice_pref = st.slider("Spice Preference:", 0, 10, int(current_spice))
            sugar_pref = st.slider("Sugar Preference:", 0, 10, int(current_sugar))
            
            submit_btn = st.form_submit_button("Update Preferences")
            
            if submit_btn:
                # Update user preferences in session state (simulating database update)
                # In a real app, this would update the database
                
                # Update dietary preference
                if 'user_preferences' not in st.session_state:
                    st.session_state.user_preferences = {}
                
                st.session_state.user_preferences['dietary'] = dietary_pref
                
                # Update weather-specific preferences
                if 'weather_preferences' not in st.session_state.user_preferences:
                    st.session_state.user_preferences['weather_preferences'] = {}
                
                st.session_state.user_preferences['weather_preferences'][weather_type] = {
                    'spice': spice_pref,
                    'sugar': sugar_pref
                }
                
                # Update recommendations based on new preferences
                st.session_state.personalized_recommendations = update_recommendations(
                    st.session_state.user_id,
                    st.session_state.weather_preference,
                    st.session_state.liked_foods,
                    st.session_state.disliked_foods,
                    st.session_state.search_history
                )
                
                st.success("Preferences updated successfully!")
    
    elif st.session_state.current_page == 'liked_foods':
        st.title("Your Liked Foods")
        
        if len(st.session_state.liked_foods) > 0:
            # Get details of liked foods
            liked_food_items = []
            for food_id in st.session_state.liked_foods:
                food_item = df_food[df_food['Food_ID'] == food_id]
                if not food_item.empty:
                    liked_food_items.append(food_item.iloc[0])
            
            # Display liked foods
            for i, food_item in enumerate(liked_food_items):
                st.write(f"### {food_item['Dish_Name']}")
                st.write(f"**Cuisine:** {food_item['Cuisine_Type']}")
                st.write(f"**Category:** {food_item['Dish_Category']}")
                st.write(f"**Type:** {food_item['Veg_Non']}")
                
                # Unlike button
                if st.button("Unlike", key=f"unlike_{i}_{food_item['Food_ID']}"):
                    st.session_state.liked_foods.remove(food_item['Food_ID'])
                    # Update recommendations after unliking
                    st.session_state.personalized_recommendations = update_recommendations(
                        st.session_state.user_id,
                        st.session_state.weather_preference,
                        st.session_state.liked_foods,
                        st.session_state.disliked_foods,
                        st.session_state.search_history
                    )
                    st.rerun()
                
                st.markdown("---")
        else:
            st.info("You haven't liked any foods yet. Start exploring recommendations and mark foods you enjoy!")
else:
    # User is not authenticated, show welcome message
    st.title("Welcome to Food Recommendation System")
    st.write("Please login or signup to get personalized food recommendations.")
    
    # Display a brief description of the app
    st.markdown("""
    ### Features:
    - Get personalized food recommendations based on your preferences
    - Discover new dishes based on your taste profile
    - Search for specific food items
    - Track your favorite foods
    - Receive recommendations based on current weather conditions
    
    Please use the sidebar to login or signup to start your culinary journey!
    """)
