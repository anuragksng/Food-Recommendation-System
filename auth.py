import streamlit as st
import time
from database.db_operations import get_user_by_username, create_user

def login():
    """
    Handle user login functionality
    """
    st.title("Login")
    
    # Create input fields
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    # Create login button
    if st.button("Login"):
        # Check credentials
        if check_credentials(username, password):
            # Set session state variables
            user = get_user_by_username(username)
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['user_id'] = user.id
            
            # Get the user's preferred weather from their preferences
            from database.db_operations import get_user_preferences
            user_prefs = get_user_preferences(user.id)
            
            if user_prefs and len(user_prefs) > 0:
                # Use the first weather preference as the default
                st.session_state['weather'] = user_prefs[0].weather_type
            else:
                # Fallback to a default weather type
                st.session_state['weather'] = 'Cold'
                
            st.success(f"Welcome back, {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def signup():
    """
    Handle user signup functionality
    """
    st.title("Sign Up")
    
    # Personal information
    with st.form(key="signup_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        # Demographics
        age_options = ["Child", "Teen", "Adult", "Senior"]
        age = st.selectbox("Age Group", age_options)
        
        gender_options = ["Male", "Female", "Other"]
        gender = st.selectbox("Gender", gender_options)
        
        # Dietary preferences
        diet_options = ["Vegetarian", "Non-Vegetarian", "Vegan", "Gluten-Free", "Keto", "Paleo"]
        dietary_preference = st.selectbox("Dietary Preference", diet_options)
        
        allergies = st.text_input("Allergies (comma-separated, leave empty if none)")
        
        # Weather-based preferences
        st.subheader("Food Preferences")
        
        # Create a dictionary to store preferences
        weather_preferences = {}
        
        # Select preferred weather type
        weather_type = st.selectbox(
            "Select your preferred weather type:",
            ["Cold", "Hot", "Rainy", "Humid"]
        )
        
        # Set preferences for the selected weather
        st.write(f"Set your preferences for {weather_type} weather:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            spice_pref = st.slider(f"Spice Preference ({weather_type})", 0, 10, 5)
        with col2:
            sugar_pref = st.slider(f"Sugar Preference ({weather_type})", 0, 10, 5)
        with col3:
            meal_pref = st.selectbox(f"Preferred Meal ({weather_type})", ["Any", "Breakfast", "Lunch", "Dinner", "Snack"])
        
        # Store preferences for selected weather
        weather_preferences[weather_type] = {"spice": spice_pref, "sugar": sugar_pref, "meal_type": meal_pref}
        
        # Use default values for other weather types
        default_meal = "Any"
        default_value = 5
        
        for w_type in ["Cold", "Hot", "Rainy", "Humid"]:
            if w_type != weather_type:
                weather_preferences[w_type] = {"spice": default_value, "sugar": default_value, "meal_type": default_meal}
        
        submit_button = st.form_submit_button("Sign Up")
        
        if submit_button:
            # Validate input
            if not username or not password:
                st.error("Username and password are required")
                return
                
            if password != confirm_password:
                st.error("Passwords do not match")
                return
                
            if username_exists(username):
                st.error("Username already exists")
                return
                
            # Create user
            user_id = create_new_user(username, password, age, gender, dietary_preference, allergies, weather_preferences)
            
            if user_id:
                st.success("Account created successfully! You can now log in.")
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['user_id'] = user_id
                
                # Set the preferred weather in the session
                st.session_state['weather'] = weather_type
                
                st.rerun()
            else:
                st.error("Failed to create account")

def check_credentials(username, password):
    """
    Check if the provided credentials are valid with retry logic
    
    In a real app, this would query a database with properly hashed passwords
    """
    if not username or not password:
        return False
    
    # Add retry logic for database connectivity
    max_retries = 3
    retry_count = 0
    backoff_factor = 2
    
    while retry_count < max_retries:
        try:
            user = get_user_by_username(username)
            return user is not None and user.password == password
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                st.error(f"Database connection error: {e}")
                return False
                
            # Exponential backoff
            wait_time = backoff_factor ** retry_count
            time.sleep(wait_time)
    
    return False

def username_exists(username):
    """
    Check if a username already exists with retry logic for database connection issues
    """
    max_retries = 3
    retry_count = 0
    backoff_factor = 2
    
    while retry_count < max_retries:
        try:
            user = get_user_by_username(username)
            return user is not None
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                st.error(f"Database connection error: {e}")
                # Return False on failure to avoid preventing signup
                return False
            
            # Exponential backoff
            wait_time = backoff_factor ** retry_count
            time.sleep(wait_time)
            
    return False

def create_new_user(username, password, age, gender, dietary_preference, allergies, weather_preferences):
    """
    Create a new user with the provided information with retry logic
    
    In a real app, this would add an entry to a database with a properly hashed password
    """
    # Format allergies string
    allergies_str = allergies if allergies else "None"
    
    # Create user in database with retry logic
    max_retries = 3
    retry_count = 0
    backoff_factor = 2
    
    while retry_count < max_retries:
        try:
            user_id = create_user(username, password, age, gender, dietary_preference, allergies_str, weather_preferences)
            return user_id
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                st.error(f"Database error creating user: {e}")
                return None
                
            # Exponential backoff
            wait_time = backoff_factor ** retry_count
            time.sleep(wait_time)
    
    return None

def check_authentication():
    """
    Check if the user is authenticated
    """
    return 'logged_in' in st.session_state and st.session_state['logged_in']