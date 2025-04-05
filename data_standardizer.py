import pandas as pd
import os

def standardize_food_data():
    """
    Standardize the food data to have consistent 'Type' values:
    - Rename 'Veg_Non' column to 'Type'
    - Standardize 'Non-Vegetarian' and variants to 'NonVegetarian'
    - Standardize everything else to 'Vegetarian'
    """
    # Read the original food CSV file
    food_file_path = 'attached_assets/food.csv'
    output_file_path = 'attached_assets/food_standardized.csv'
    
    print(f"Reading food data from {food_file_path}")
    df_food = pd.read_csv(food_file_path)
    
    original_count = len(df_food)
    print(f"Original row count: {original_count}")
    
    # Create a copy of the dataframe
    df_standardized = df_food.copy()
    
    # Analyze the Veg_Non column before changes
    print("\nCounts of values in 'Veg_Non' column before standardization:")
    print(df_standardized['Veg_Non'].value_counts().to_string())
    
    # Handle non-vegetarian values
    non_veg_values = ['Non-Vegetarian', 'Non-Veg', 'non-vegetarian', 'non-veg']
    mask_non_veg = df_standardized['Veg_Non'].isin(non_veg_values)
    df_standardized.loc[mask_non_veg, 'Veg_Non'] = 'NonVegetarian'
    
    # Handle vegetarian values
    veg_values = ['Vegetarian', 'Veg', 'vegetarian', 'veg']
    mask_veg = df_standardized['Veg_Non'].isin(veg_values)
    df_standardized.loc[mask_veg, 'Veg_Non'] = 'Vegetarian'
    
    # For all other values that are neither clearly veg nor non-veg, set as 'Vegetarian' by default
    # This is a simplification - in a real app, these would need manual review
    mask_other = ~(mask_non_veg | mask_veg)
    print(f"\nFound {mask_other.sum()} rows with values that are neither clearly veg nor non-veg")
    
    # For debugging, print these ambiguous values before changing them
    if mask_other.sum() > 0:
        print("Ambiguous values:")
        print(df_standardized.loc[mask_other, 'Veg_Non'].value_counts().to_string())
    
    # For simplicity, set all ambiguous values to 'Vegetarian'
    # In a real application, these would need manual review
    df_standardized.loc[mask_other, 'Veg_Non'] = 'Vegetarian'
    
    # Create a new 'Type' column instead of renaming, to keep both for backward compatibility
    df_standardized['Type'] = df_standardized['Veg_Non']
    
    # Analyze the Type column after changes
    print("\nCounts of values in 'Type' column after standardization:")
    print(df_standardized['Type'].value_counts().to_string())
    
    # Confirm both columns exist
    print("\nColumns in standardized dataframe:")
    print(df_standardized.columns.tolist())
    
    # Save the standardized dataframe to a new CSV file
    df_standardized.to_csv(output_file_path, index=False)
    print(f"\nStandardized data saved to {output_file_path}")
    
    return df_standardized

if __name__ == "__main__":
    standardize_food_data()