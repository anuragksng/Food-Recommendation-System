import streamlit as st
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
        st.subheader("Preferences by Weather")
        
        # Create a dictionary to store preferences
        weather_preferences = {}
        
        # Cold weather preferences
        st.write("Cold Weather")
        col1, col2, col3 = st.columns(3)
        with col1:
            cold_spice = st.slider("Spice Preference (Cold)", 0, 10, 5)
        with col2:
            cold_sugar = st.slider("Sugar Preference (Cold)", 0, 10, 5)
        with col3:
            cold_meal = st.selectbox("Preferred Meal (Cold)", ["Breakfast", "Lunch", "Dinner", "Snack"])
        weather_preferences["Cold"] = {"spice": cold_spice, "sugar": cold_sugar, "meal_type": cold_meal}
        
        # Hot weather preferences
        st.write("Hot Weather")
        col1, col2, col3 = st.columns(3)
        with col1:
            hot_spice = st.slider("Spice Preference (Hot)", 0, 10, 5)
        with col2:
            hot_sugar = st.slider("Sugar Preference (Hot)", 0, 10, 5)
        with col3:
            hot_meal = st.selectbox("Preferred Meal (Hot)", ["Breakfast", "Lunch", "Dinner", "Snack"])
        weather_preferences["Hot"] = {"spice": hot_spice, "sugar": hot_sugar, "meal_type": hot_meal}
        
        # Rainy weather preferences
        st.write("Rainy Weather")
        col1, col2, col3 = st.columns(3)
        with col1:
            rainy_spice = st.slider("Spice Preference (Rainy)", 0, 10, 5)
        with col2:
            rainy_sugar = st.slider("Sugar Preference (Rainy)", 0, 10, 5)
        with col3:
            rainy_meal = st.selectbox("Preferred Meal (Rainy)", ["Breakfast", "Lunch", "Dinner", "Snack"])
        weather_preferences["Rainy"] = {"spice": rainy_spice, "sugar": rainy_sugar, "meal_type": rainy_meal}
        
        # Humid weather preferences
        st.write("Humid Weather")
        col1, col2, col3 = st.columns(3)
        with col1:
            humid_spice = st.slider("Spice Preference (Humid)", 0, 10, 5)
        with col2:
            humid_sugar = st.slider("Sugar Preference (Humid)", 0, 10, 5)
        with col3:
            humid_meal = st.selectbox("Preferred Meal (Humid)", ["Breakfast", "Lunch", "Dinner", "Snack"])
        weather_preferences["Humid"] = {"spice": humid_spice, "sugar": humid_sugar, "meal_type": humid_meal}
        
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
                st.rerun()
            else:
                st.error("Failed to create account")

def check_credentials(username, password):
    """
    Check if the provided credentials are valid
    
    In a real app, this would query a database with properly hashed passwords
    For this demo, we'll simulate the verification process
    """
    if not username or not password:
        return False
        
    user = get_user_by_username(username)
    
    if user and user.password == password:
        return True
        
    return False

def username_exists(username):
    """
    Check if a username already exists
    """
    user = get_user_by_username(username)
    return user is not None

def create_new_user(username, password, age, gender, dietary_preference, allergies, weather_preferences):
    """
    Create a new user with the provided information
    
    In a real app, this would add an entry to a database with a properly hashed password
    For this demo, we'll simulate the process
    """
    # Format allergies string
    allergies_str = allergies if allergies else "None"
    
    # Create user in database
    user_id = create_user(username, password, age, gender, dietary_preference, allergies_str, weather_preferences)
    
    return user_id

def check_authentication():
    """
    Check if the user is authenticated
    """
    return 'logged_in' in st.session_state and st.session_state['logged_in']