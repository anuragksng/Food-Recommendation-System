"""
Strict Food Type Filtering Module

This module provides direct filtering functions to ensure users only see food items that exactly match
their dietary preferences. Only two dietary types are supported: Vegetarian and NonVegetarian.
"""

def strict_type_filter(food_items, dietary_preference):
    """
    Filter food items by directly matching food type with user's dietary preference
    
    Args:
        food_items: List of food item dictionaries
        dietary_preference: User's dietary preference
        
    Returns:
        list: Filtered food items
    """
    if not food_items:
        return []
    
    filtered_items = []
    print(f"Strict filtering {len(food_items)} items based on preference '{dietary_preference}'")
    
    # Normalize preference for comparison
    is_vegetarian = dietary_preference.lower().strip() == 'vegetarian'
    
    # Only include items that EXACTLY match the dietary preference
    for item in food_items:
        # Use Type column if available, otherwise fall back to Veg_Non
        type_key = 'Type' if 'Type' in item else 'Veg_Non'
        
        # Skip items with no food type information
        if type_key not in item or item[type_key] is None or item[type_key] == "":
            continue
            
        # Get food type and standardize it
        food_type = str(item[type_key]).strip()
        
        if is_vegetarian:
            # For vegetarian users, only include Vegetarian items
            if food_type == 'Vegetarian':
                filtered_items.append(item)
        else:
            # For non-vegetarian users, only include NonVegetarian items
            if food_type == 'NonVegetarian':
                filtered_items.append(item)
    
    print(f"Strict filtering results: {len(filtered_items)} items match preference '{dietary_preference}'")
    return filtered_items

def apply_strict_filtering(recommendations, dietary_preference):
    """
    Apply strict food type filtering as a final safeguard on recommendations
    
    Args:
        recommendations: List of food item dictionaries
        dietary_preference: User's dietary preference
        
    Returns:
        list: Filtered food items
    """
    # Always apply strict filtering regardless of preference
    return strict_type_filter(recommendations, dietary_preference)