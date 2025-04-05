"""
Strict Food Type Filtering Module

This module provides direct filtering functions to ensure users only see food items that exactly match
their dietary preferences.
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
        
    if not dietary_preference or dietary_preference.lower() in ['none', 'non-vegetarian', 'any']:
        return food_items
    
    filtered_items = []
    print(f"Strict filtering {len(food_items)} items based on preference '{dietary_preference}'")
    
    # Normalize preference for comparison
    preference_lower = dietary_preference.lower().strip()
    
    # Map preference variations to standard forms for exact matching
    preference_map = {
        'vegetarian': ['veg', 'vegetarian'],
        'vegan': ['vegan'],
        'gluten-free': ['gluten-free']
    }
    
    # Get the allowed values for this preference
    allowed_types = preference_map.get(preference_lower, [preference_lower])
    
    # Only include items that EXACTLY match the allowed types
    for item in food_items:
        # Skip items with no food type information
        if 'Veg_Non' not in item or item['Veg_Non'] is None or item['Veg_Non'] == "":
            continue
            
        # Normalize the food type for comparison
        food_type = str(item['Veg_Non']).lower().strip()
        
        # Only include if the food type EXACTLY matches one of the allowed types
        if food_type in allowed_types:
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
    if not dietary_preference or dietary_preference.lower() in ['none', 'non-vegetarian', 'any']:
        return recommendations
        
    # For vegetarian/vegan users, apply strict type matching
    if dietary_preference.lower() in ['vegetarian', 'vegan']:
        return strict_type_filter(recommendations, dietary_preference)
    
    # For other dietary preferences, use the regular filtering
    return recommendations