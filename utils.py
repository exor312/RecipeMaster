import json
import pandas as pd
import os
import glob
from typing import Dict, List, Optional
import hashlib

def generate_unique_id(recipe: Dict, seen_ids: set) -> int:
    """
    Generate a unique ID for a recipe based on its content
    """
    # Start with a hash of the recipe name and ingredients to create a base number
    content = f"{recipe['name']}{''.join(recipe['ingredients'])}".encode('utf-8')
    hash_num = int(hashlib.md5(content).hexdigest(), 16)
    
    # Get a number between 1 and 1000000 that isn't in seen_ids
    base_id = (hash_num % 1000000) + 1
    new_id = base_id
    
    # If the ID is already taken, increment until we find an unused one
    while new_id in seen_ids:
        new_id += 1
        if new_id > 1000000:
            new_id = 1  # wrap around if we somehow exceed our range
    
    return new_id

def load_recipes(data_dir: str = 'data/recipe') -> pd.DataFrame:
    """
    Load recipes from all JSON files in the data/recipe directory and convert to DataFrame
    """
    all_recipes = []
    seen_ids = set()
    warnings = []
    
    try:
        # Create data/recipe directory structure if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Find all JSON files in the recipes directory
        json_files = glob.glob(os.path.join(data_dir, '*.json'))
        
        if not json_files:
            raise FileNotFoundError(
                f"No recipe files found in the {data_dir} directory. "
                "To get started, add your recipe JSON files to this folder."
            )

        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Handle both single recipe and recipe collection formats
                    recipes = data if isinstance(data, list) else data.get('recipes', [])
                    if not isinstance(recipes, list):
                        recipes = [recipes]
                    
                    for recipe in recipes:
                        # Skip invalid recipes
                        if not isinstance(recipe, dict):
                            warnings.append(f"Skipped invalid recipe format in {file_path}")
                            continue
                            
                        # Check for required fields
                        required_fields = ['name', 'cuisine', 'difficulty', 'prep_time', 'cook_time', 
                                         'servings', 'ingredients', 'instructions']
                        missing_fields = [field for field in required_fields if field not in recipe]
                        if missing_fields:
                            warnings.append(
                                f"Recipe '{recipe.get('name', 'Unknown')}' in {file_path} "
                                f"is missing required fields: {', '.join(missing_fields)}"
                            )
                            continue

                        # Ensure categories exist
                        if 'categories' not in recipe:
                            recipe['categories'] = []

                        # Handle recipe ID
                        recipe_id = recipe.get('id')
                        if recipe_id is None:
                            # Generate a new unique ID
                            recipe_id = generate_unique_id(recipe, seen_ids)
                            recipe['id'] = recipe_id
                            warnings.append(
                                f"Auto-generated ID {recipe_id} for recipe '{recipe['name']}' "
                                f"in {file_path}"
                            )
                        elif recipe_id in seen_ids:
                            # Handle duplicate ID by generating a new one
                            new_id = generate_unique_id(recipe, seen_ids)
                            warnings.append(
                                f"Found duplicate ID {recipe_id} for recipe '{recipe['name']}' "
                                f"in {file_path}. Assigned new ID: {new_id}"
                            )
                            recipe['id'] = new_id
                            recipe_id = new_id
                            
                        seen_ids.add(recipe_id)
                        all_recipes.append(recipe)
                        
            except json.JSONDecodeError:
                warnings.append(f"Could not read {file_path} - the file contains invalid JSON format")
            except Exception as e:
                warnings.append(f"Error processing {file_path}: {str(e)}")

        if not all_recipes:
            raise ValueError(
                "No valid recipes found. Please ensure your recipe files are in the correct format "
                "and contain all required fields: name, cuisine, difficulty, prep_time, cook_time, "
                "servings, ingredients, and instructions."
            )

        df = pd.DataFrame(all_recipes)
        
        # If there were any warnings, log them but continue if we have valid recipes
        if warnings:
            print("\nRecipe Loading Summary:")
            for warning in warnings:
                print(f"- {warning}")
            print(f"\nSuccessfully loaded {len(all_recipes)} valid recipes.")
                
        return df

    except Exception as e:
        raise Exception(f"Failed to load recipes: {str(e)}")

def filter_recipes(df: pd.DataFrame, 
                  search_term: str = "", 
                  cuisine: Optional[str] = None,
                  category: Optional[str] = None) -> pd.DataFrame:
    """
    Filter recipes based on search term, cuisine, and category
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

    if category and category != "All":
        filtered_df = filtered_df[filtered_df['categories'].apply(lambda x: category in x)]

    return filtered_df

def format_recipe_details(recipe: Dict) -> str:
    """
    Format recipe details for display
    """
    details = f"""
    ### {recipe['name']}
    
    #### Preparation Time: {recipe['prep_time']}
    #### Cooking Time: {recipe['cook_time']}
    #### Servings: {recipe['servings']}
    #### Difficulty: {recipe['difficulty']}
    #### Cuisine: {recipe['cuisine']}
    #### Categories: {', '.join(recipe.get('categories', []))}
    
    ## Ingredients
    """
    
    for ingredient in recipe['ingredients']:
        details += f"- {ingredient}\n"
    
    details += "\n## Instructions\n"
    
    for i, instruction in enumerate(recipe['instructions'], 1):
        details += f"{i}. {instruction}\n"
        
    return details
