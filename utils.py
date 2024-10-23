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
    content = f"{recipe['name']}{''.join(recipe['ingredients'])}".encode('utf-8')
    hash_num = int(hashlib.md5(content).hexdigest(), 16)
    base_id = (hash_num % 1000000) + 1
    new_id = base_id
    
    while new_id in seen_ids:
        new_id += 1
        if new_id > 1000000:
            new_id = 1
    
    return new_id

def parse_filipino_recipe(recipe: Dict) -> Dict:
    """
    Parse Filipino recipe format and convert to standard format
    """
    # Extract cooking time and convert to standard format
    cook_time = recipe.get('cooking_time', '30 minutes')
    
    # Set default prep time as 15 minutes if not specified
    prep_time = '15 minutes'
    
    # Map the fields to our standard format
    standardized_recipe = {
        'name': recipe.get('title', 'Unknown Filipino Recipe'),
        'cuisine': 'Filipino',
        'difficulty': 'Medium',  # Default difficulty
        'prep_time': prep_time,
        'cook_time': cook_time,
        'servings': recipe.get('servings', '4'),  # Default to 4 servings if N/A
        'ingredients': [ing.replace('▢ ', '') for ing in recipe.get('ingredients', [])],
        'instructions': recipe.get('instructions', []),
        'categories': [recipe.get('category', 'Filipino Dishes')]
    }
    
    return standardized_recipe

def load_recipes(data_dir: str = 'data/recipe') -> pd.DataFrame:
    """
    Load recipes from all JSON files in the data/recipe directory and convert to DataFrame
    """
    all_recipes = []
    seen_ids = set()
    warnings = []
    
    try:
        os.makedirs(data_dir, exist_ok=True)
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
                    
                    # Check if this is a Filipino recipe file
                    is_filipino = 'filipino_recipes_page_' in os.path.basename(file_path).lower()
                    
                    # Handle both single recipe and recipe collection formats
                    recipes = data if isinstance(data, list) else data.get('recipes', [])
                    if not isinstance(recipes, list):
                        recipes = [recipes]
                    
                    for recipe in recipes:
                        if not isinstance(recipe, dict):
                            warnings.append(f"Skipped invalid recipe format in {file_path}")
                            continue
                        
                        # Parse Filipino recipes differently
                        if is_filipino:
                            recipe = parse_filipino_recipe(recipe)
                        
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
                            recipe_id = generate_unique_id(recipe, seen_ids)
                            recipe['id'] = recipe_id
                            warnings.append(
                                f"Auto-generated ID {recipe_id} for recipe '{recipe['name']}' "
                                f"in {file_path}"
                            )
                        elif recipe_id in seen_ids:
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
        search_term = search_term.lower()
        name_mask = filtered_df['name'].str.lower().str.contains(search_term, na=False)
        ingredients_mask = filtered_df['ingredients'].apply(
            lambda x: any(search_term in ingredient.lower() for ingredient in x)
        )
        filtered_df = filtered_df[name_mask | ingredients_mask]

    if cuisine and cuisine != "All":
        filtered_df = filtered_df[filtered_df['cuisine'] == cuisine]

    if category and category != "All":
        filtered_df = filtered_df[filtered_df['categories'].apply(lambda x: category in x if isinstance(x, list) else False)]

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
