import streamlit as st
import pandas as pd
import numpy as np
import random
from data_loader import load_data
from recommender import generate_initial_recommendations

def login():
    """
    Handle user login functionality
    """
    st.subheader("Login to your account")
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    login_button = st.button("Login")
    
    if login_button:
        if not username or not password:
            st.error("Please enter both username and password.")
            return
        
        # Simulate checking credentials against a database
        # In a real app, you would check against a secure database with hashed passwords
        valid_login, user_data = check_credentials(username, password)
        
        if valid_login:
            # Set session state variables for the authenticated user
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_id = user_data['user_id']
            
            # Load user preferences from data
            df_user, _, _, df_user_preferences, _ = load_data()
            
            # Get user preferences
            user_info = df_user[df_user['User_ID'] == st.session_state.user_id].iloc[0]
            user_prefs = df_user_preferences[df_user_preferences['User_ID'] == st.session_state.user_id]
            
            # Store user preferences in session state
            st.session_state.user_preferences = {
                'dietary': user_info['Dietary_Preferences'],
                'age': user_info['Age'],
                'gender': user_info['Gender'],
                'allergies': user_info['Allergies'],
                'weather_preferences': {}
            }
            
            # Add weather-specific preferences
            for _, row in user_prefs.iterrows():
                st.session_state.user_preferences['weather_preferences'][row['Weather_Type']] = {
                    'spice': row['Spice_Preference'],
                    'sugar': row['Sugar_Preference'],
                    'meal_type': row['Meal_Type']
                }
            
            # Generate initial recommendations
            st.session_state.personalized_recommendations = generate_initial_recommendations(
                st.session_state.user_id,
                st.session_state.weather_preference,
                st.session_state.user_preferences
            )
            
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password. Please try again.")

def signup():
    """
    Handle user signup functionality
    """
    st.subheader("Create a new account")
    
    with st.form(key="signup_form"):
        username = st.text_input("Username", key="signup_username")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        # User preferences
        st.subheader("Your Preferences")
        
        age_options = ["Child", "Teen", "Adult", "Senior"]
        age = st.selectbox("Age Group", age_options)
        
        gender_options = ["Male", "Female", "Other"]
        gender = st.selectbox("Gender", gender_options)
        
        dietary_options = ["Non-Vegetarian", "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Paleo"]
        dietary_preference = st.selectbox("Dietary Preference", dietary_options)
        
        allergens = st.multiselect(
            "Allergies (if any)",
            ["None", "Dairy", "Gluten", "Nuts", "Eggs", "Soy", "Shellfish"]
        )
        
        # Weather preferences
        st.subheader("Weather Preferences")
        
        weather_types = ['Cold', 'Hot', 'Rainy', 'Humid', 'Windy']
        
        # Create tabs for each weather type
        tabs = st.tabs(weather_types)
        
        weather_preferences = {}
        
        for i, weather in enumerate(weather_types):
            with tabs[i]:
                meal_options = ["Breakfast", "Lunch", "Dinner"]
                weather_preferences[weather] = {
                    'meal_type': st.selectbox(f"Preferred Meal Type for {weather} Weather", meal_options, key=f"meal_{weather}"),
                    'spice': st.slider(f"Spice Preference for {weather} Weather (0-10)", 0, 10, 5, key=f"spice_{weather}"),
                    'sugar': st.slider(f"Sugar Preference for {weather} Weather (0-10)", 0, 10, 5, key=f"sugar_{weather}")
                }
        
        signup_button = st.form_submit_button("Sign Up")
        
        if signup_button:
            if not username or not password:
                st.error("Please enter both username and password.")
                return
            
            if password != confirm_password:
                st.error("Passwords do not match.")
                return
            
            # Check if username already exists
            if username_exists(username):
                st.error("Username already exists. Please choose a different one.")
                return
            
            # Create new user
            new_user_id = create_user(username, password, age, gender, dietary_preference, allergens, weather_preferences)
            
            if new_user_id:
                st.success("Account created successfully! Please login.")
                # Clear the form
                st.rerun()
            else:
                st.error("Error creating account. Please try again.")

def check_credentials(username, password):
    """
    Check if the provided credentials are valid
    
    In a real app, this would query a database with properly hashed passwords
    For this demo, we'll simulate the verification process
    """
    # Simulate a database check
    # In a real app, you would check against a database with hashed passwords
    
    # Let's assume we have a simple dictionary mapping usernames to user data
    # This is just for demonstration - in a real app, use proper authentication methods
    
    # For demo purposes, we'll consider the first 20 users from df_user as existing accounts
    # with password same as username for simplicity
    df_user, _, _, _, _ = load_data()
    
    valid_users = {}
    for i in range(min(20, len(df_user))):
        user_row = df_user.iloc[i]
        user_id = user_row['User_ID']
        # For simplicity, username is "user{user_id}" and password is the same
        username_key = f"user{user_id}"
        valid_users[username_key] = {
            'password': username_key,  # In a real app, this would be a hashed password
            'user_id': user_id
        }
    
    # Add a default test account
    valid_users['test'] = {
        'password': 'test',
        'user_id': 1
    }
    
    if username in valid_users and valid_users[username]['password'] == password:
        return True, valid_users[username]
    
    return False, None

def username_exists(username):
    """
    Check if a username already exists
    """
    # For demo purposes
    # In a real app, this would query a database
    df_user, _, _, _, _ = load_data()
    
    valid_users = [f"user{user_id}" for user_id in df_user['User_ID'].unique()[:20]]
    valid_users.append('test')
    
    return username in valid_users

def create_user(username, password, age, gender, dietary_preference, allergies, weather_preferences):
    """
    Create a new user with the provided information
    
    In a real app, this would add an entry to a database with a properly hashed password
    For this demo, we'll simulate the process
    """
    # Simulate creating a user in the database
    # For demo purposes, we'll generate a random user ID
    # In a real app, this would be handled by the database
    
    df_user, _, _, _, _ = load_data()
    
    # Generate a new user ID (for demo purposes, just use max + 1)
    new_user_id = df_user['User_ID'].max() + 1
    
    # Format allergies for storage
    allergies_str = ", ".join(allergies) if allergies else "None"
    
    # In a real app, this information would be stored in a database
    # For this demo, we'll just keep it in the session state
    
    # Store user information
    if 'users' not in st.session_state:
        st.session_state.users = {}
    
    st.session_state.users[username] = {
        'password': password,  # In a real app, this would be hashed
        'user_id': new_user_id,
        'age': age,
        'gender': gender,
        'dietary_preference': dietary_preference,
        'allergies': allergies_str,
        'weather_preferences': weather_preferences
    }
    
    return new_user_id

def check_authentication():
    """
    Check if the user is authenticated
    """
    return st.session_state.authenticated if 'authenticated' in st.session_state else False
