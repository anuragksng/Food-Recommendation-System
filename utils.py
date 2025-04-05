import streamlit as st
from database.db_operations import get_user_by_username

def display_food_item(food_item, index):
    """
    Display a food item in a card layout
    
    Args:
        food_item: Dictionary containing food item details
        index: Index of the food item for unique keys
    """
    # Create a bordered box for each food item
    with st.container():
        st.markdown(f"""
        <div style="padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; background-color: white;">
            <h3 style="color: #1E88E5;">{food_item['Dish_Name']}</h3>
            <p><b>Cuisine:</b> {food_item['Cuisine_Type']}</p>
            <p><b>Type:</b> {food_item.get('Type', food_item.get('Veg_Non', 'Unknown'))}</p>
            <p><b>Category:</b> {food_item['Dish_Category']}</p>
            <p>
                <span style="display: inline-block; width: 150px;">
                    <b>Spice Level:</b> {'🌶️' * food_item['Spice_Level']}
                </span>
                <span style="display: inline-block; width: 150px;">
                    <b>Sugar Level:</b> {'🍬' * food_item['Sugar_Level']}
                </span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"👍 Like", key=f"like_{index}_{food_item['Food_ID']}"):
                return "like"
        with col2:
            if st.button(f"👎 Dislike", key=f"dislike_{index}_{food_item['Food_ID']}"):
                return "dislike"
        with col3:
            if st.button(f"ℹ️ Details", key=f"details_{index}_{food_item['Food_ID']}"):
                return "details"
    
    return None

def display_food_details(food_item):
    """
    Display detailed information for a food item
    
    Args:
        food_item: Dictionary containing food item details
    """
    st.title(food_item['Dish_Name'])
    
    # Display main info
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Cuisine:** {food_item['Cuisine_Type']}")
        # Use Type if available, otherwise fall back to Veg_Non
        type_value = food_item.get('Type', food_item.get('Veg_Non', 'Unknown'))
        st.write(f"**Type:** {type_value}")
        st.write(f"**Category:** {food_item['Dish_Category']}")
        st.write(f"**Best Weather:** {food_item['Weather_Type']}")
    
    with col2:
        st.write("**Spice Level:**")
        st.progress(food_item['Spice_Level'] / 10)
        st.write("**Sugar Level:**")
        st.progress(food_item['Sugar_Level'] / 10)
    
    # Display description
    st.subheader("Description")
    st.markdown(food_item['Describe'], unsafe_allow_html=True)
    
    # Add a back button
    if st.button("← Back to Recommendations"):
        return True
    
    return False

def get_user_name(user_id):
    """
    Get the username for a given user ID
    
    Args:
        user_id: The ID of the user
        
    Returns:
        str: The username (or default if not found)
    """
    user = get_user_by_username(user_id)
    if user:
        return user.username
    return f"User_{user_id}"

def format_allergies(allergies_str):
    """
    Format allergies string for display
    
    Args:
        allergies_str: String containing allergies
        
    Returns:
        str: Formatted allergies string
    """
    if not allergies_str or allergies_str.lower() == "none":
        return "None"
    
    allergies = [a.strip() for a in allergies_str.split(',')]
    return ", ".join(allergies)