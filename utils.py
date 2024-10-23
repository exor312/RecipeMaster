import json
import pandas as pd
from typing import Dict, List, Optional

def load_recipes(file_path: str) -> pd.DataFrame:
    """
    Load recipes from JSON file and convert to DataFrame
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            recipes = data.get('recipes', [])
            return pd.DataFrame(recipes)
    except FileNotFoundError:
        raise FileNotFoundError("Recipe data file not found")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in recipe file")

def filter_recipes(df: pd.DataFrame, 
                  search_term: str = "", 
                  cuisine: Optional[str] = None) -> pd.DataFrame:
    """
    Filter recipes based on search term and cuisine
    """
    if df.empty:
        return df

    filtered_df = df.copy()
    
    if search_term:
        # Search in name and ingredients
        search_term = search_term.lower()
        name_mask = filtered_df['name'].str.lower().str.contains(search_term, na=False)
        ingredients_mask = filtered_df['ingredients'].apply(
            lambda x: any(search_term in ingredient.lower() for ingredient in x)
        )
        filtered_df = filtered_df[name_mask | ingredients_mask]

    if cuisine and cuisine != "All":
        filtered_df = filtered_df[filtered_df['cuisine'] == cuisine]

    return filtered_df

def format_recipe_details(recipe: Dict) -> str:
    """
    Format recipe details for display
    """
    details = f"""
    ### Preparation Time: {recipe['prep_time']}
    ### Cooking Time: {recipe['cook_time']}
    ### Servings: {recipe['servings']}
    ### Difficulty: {recipe['difficulty']}
    ### Cuisine: {recipe['cuisine']}
    
    ## Ingredients
    """
    
    for ingredient in recipe['ingredients']:
        details += f"- {ingredient}\n"
    
    details += "\n## Instructions\n"
    
    for i, instruction in enumerate(recipe['instructions'], 1):
        details += f"{i}. {instruction}\n"
        
    return details
