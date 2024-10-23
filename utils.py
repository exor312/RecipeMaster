import json
import pandas as pd
import os
import glob
from typing import Dict, List, Optional

def load_recipes(data_dir: str = 'data/recipe') -> pd.DataFrame:
    """
    Load recipes from all JSON files in the data/recipe directory and convert to DataFrame
    
    Args:
        data_dir (str): Directory containing recipe JSON files
        
    Returns:
        pd.DataFrame: Combined DataFrame of all recipes
    """
    all_recipes = []
    seen_ids = set()
    errors = []

    try:
        # Create data/recipe directory structure if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Find all JSON files in the recipes directory
        json_files = glob.glob(os.path.join(data_dir, '*.json'))
        
        if not json_files:
            raise FileNotFoundError(f"No JSON recipe files found in {data_dir}. Please add recipe JSON files to the {data_dir} directory.")

        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Handle both single recipe and recipe collection formats
                    recipes = data if isinstance(data, list) else data.get('recipes', [])
                    if not isinstance(recipes, list):
                        recipes = [recipes]
                    
                    # Check for duplicate IDs
                    for recipe in recipes:
                        recipe_id = recipe.get('id')
                        if recipe_id is None:
                            errors.append(f"Recipe without ID found in {file_path}")
                            continue
                            
                        if recipe_id in seen_ids:
                            errors.append(f"Duplicate recipe ID {recipe_id} found in {file_path}")
                            continue
                            
                        seen_ids.add(recipe_id)
                        all_recipes.append(recipe)
                        
            except json.JSONDecodeError:
                errors.append(f"Invalid JSON format in {file_path}")
            except Exception as e:
                errors.append(f"Error processing {file_path}: {str(e)}")

        if not all_recipes:
            raise ValueError("No valid recipes found in any file. Please ensure your JSON files contain valid recipe data.")

        df = pd.DataFrame(all_recipes)
        
        # Ensure required columns exist
        required_columns = ['name', 'cuisine', 'difficulty', 'prep_time', 'cook_time', 'servings', 'ingredients', 'instructions']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns in recipe data: {', '.join(missing_columns)}")
        
        # If there were any errors, log them but continue if we have valid recipes
        if errors:
            print("Warnings while loading recipes:")
            for error in errors:
                print(f"- {error}")
                
        return df

    except Exception as e:
        raise Exception(f"Failed to load recipes: {str(e)}")

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

    return filtered_df.copy()  # Return a copy to avoid SettingWithCopyWarning

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
