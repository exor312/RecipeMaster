import json
import pandas as pd
import os
import glob
from typing import Dict, List, Optional, Set
import hashlib
import streamlit as st

@st.cache_data
def load_recipes(data_dir: str = 'data/recipe') -> pd.DataFrame:
    """
    Load recipes from all JSON files in the data/recipe directory and convert to DataFrame
    Cached using st.cache_data for better performance
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
                    
                    is_filipino = 'filipino_recipes_page_' in os.path.basename(file_path).lower()
                    
                    recipes = data if isinstance(data, list) else data.get('recipes', [])
                    if not isinstance(recipes, list):
                        recipes = [recipes]
                    
                    for recipe in recipes:
                        if not isinstance(recipe, dict):
                            warnings.append(f"Skipped invalid recipe format in {file_path}")
                            continue
                        
                        if is_filipino:
                            recipe = parse_filipino_recipe(recipe)
                        
                        required_fields = ['name', 'difficulty', 'prep_time', 'cook_time', 
                                       'servings', 'ingredients', 'instructions']
                        missing_fields = [field for field in required_fields if field not in recipe]
                        
                        if missing_fields:
                            warnings.append(
                                f"Recipe '{recipe.get('name', 'Unknown')}' in {file_path} "
                                f"is missing required fields: {', '.join(missing_fields)}"
                            )
                            continue

                        if 'categories' not in recipe:
                            recipe['categories'] = []

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
                        all_recipes.append({
                            'id': recipe['id'],
                            'name': recipe['name'],
                            'difficulty': recipe['difficulty'],
                            'categories': recipe['categories'],
                            'preview_data': recipe
                        })
                        
            except json.JSONDecodeError:
                warnings.append(f"Could not read {file_path} - the file contains invalid JSON format")
            except Exception as e:
                warnings.append(f"Error processing {file_path}: {str(e)}")

        if not all_recipes:
            raise ValueError(
                "No valid recipes found. Please ensure your recipe files are in the correct format "
                "and contain all required fields."
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

def generate_unique_id(recipe: Dict, seen_ids: set) -> int:
    """Generate a unique ID for a recipe based on its content"""
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
    """Parse Filipino recipe format and convert to standard format"""
    cook_time = recipe.get('cooking_time', '30 minutes')
    prep_time = '15 minutes'
    
    standardized_recipe = {
        'name': recipe.get('title', 'Unknown Filipino Recipe'),
        'difficulty': 'Medium',
        'prep_time': prep_time,
        'cook_time': cook_time,
        'servings': recipe.get('servings', '4'),
        'ingredients': [ing.replace('▢ ', '') for ing in recipe.get('ingredients', [])],
        'instructions': recipe.get('instructions', []),
        'categories': [recipe.get('category', 'Filipino Dishes')]
    }
    
    return standardized_recipe

def filter_recipes(df: pd.DataFrame, 
                  search_term: str = "", 
                  difficulty: Optional[str] = None,
                  category: Optional[str] = None,
                  show_favorites: bool = False,
                  favorites: Optional[Set[int]] = None,
                  page: int = 1,
                  per_page: int = 10) -> tuple[pd.DataFrame, int]:
    """
    Filter recipes based on search term, difficulty, category, and favorites
    Returns filtered DataFrame and total number of pages
    """
    if df.empty:
        return df, 0

    with st.spinner('Filtering recipes...'):
        filtered_df = df.copy()

        if show_favorites and favorites is not None:
            filtered_df = filtered_df[filtered_df['id'].isin(favorites)]
            
        if search_term:
            search_term = search_term.lower()
            name_mask = filtered_df['name'].str.lower().str.contains(search_term, na=False)
            filtered_df = filtered_df[name_mask]

        if difficulty and difficulty != "All":
            filtered_df = filtered_df[filtered_df['difficulty'] == difficulty]

        if category and category != "All":
            filtered_df = filtered_df[filtered_df['categories'].apply(lambda x: category in x if isinstance(x, list) else False)]

        total_recipes = len(filtered_df)
        total_pages = (total_recipes + per_page - 1) // per_page

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_df = filtered_df.iloc[start_idx:end_idx]

        return paginated_df, total_pages

def format_recipe_details(recipe: Dict) -> str:
    """Format recipe details for display with improved layout"""
    if 'preview_data' in recipe:
        recipe = recipe['preview_data']

    # Build CSS styles
    css = """
    <style>
        .recipe-title {
            color: #1f1f1f;
            font-size: 2.5em;
            margin-bottom: 1em;
            text-align: center;
        }
        .recipe-info {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1em;
            margin: 2em 0;
            padding: 1em;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        .info-item {
            text-align: center;
            padding: 1em;
        }
        .info-label {
            font-weight: bold;
            color: #666;
            margin-bottom: 0.5em;
        }
        .info-value {
            font-size: 1.2em;
            color: #333;
        }
        .ingredients-section {
            background-color: #fff;
            padding: 2em;
            border-radius: 8px;
            margin: 2em 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .ingredients-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1em;
            margin-top: 1em;
        }
        .ingredient-item {
            padding: 0.8em;
            background-color: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #FF4B4B;
            margin: 0.5em 0;
        }
        .instructions-section {
            background-color: #fff;
            padding: 2em;
            border-radius: 8px;
            margin: 2em 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .instruction-step {
            margin: 1em 0;
            padding: 1em;
            background-color: #f8f9fa;
            border-radius: 6px;
            display: flex;
            align-items: flex-start;
        }
        .step-number {
            background-color: #FF4B4B;
            color: white;
            min-width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 1em;
        }
        .categories-section {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5em;
            margin: 1em 0;
        }
        .category-tag {
            background-color: #FF4B4B;
            color: white;
            padding: 0.3em 0.8em;
            border-radius: 15px;
            font-size: 0.9em;
        }
    </style>
    """

    # Build HTML sections
    title_html = f'<div class="recipe-title">{recipe["name"]}</div>'
    
    categories_html = '<div class="categories-section">'
    categories_html += ''.join(f'<span class="category-tag">{cat}</span>' 
                             for cat in recipe.get('categories', []))
    categories_html += '</div>'
    
    info_html = (
        '<div class="recipe-info">'
        f'<div class="info-item">'
        f'<div class="info-label">Prep Time</div>'
        f'<div class="info-value">{recipe["prep_time"]}</div>'
        '</div>'
        f'<div class="info-item">'
        f'<div class="info-label">Cook Time</div>'
        f'<div class="info-value">{recipe["cook_time"]}</div>'
        '</div>'
        f'<div class="info-item">'
        f'<div class="info-label">Servings</div>'
        f'<div class="info-value">{recipe["servings"]}</div>'
        '</div>'
        f'<div class="info-item">'
        f'<div class="info-label">Difficulty</div>'
        f'<div class="info-value">{recipe["difficulty"]}</div>'
        '</div>'
        '</div>'
    )
    
    ingredients_html = '<div class="ingredients-section">'
    ingredients_html += '<h2>Ingredients</h2>'
    ingredients_html += '<div class="ingredients-grid">'
    ingredients_html += ''.join(
        f'<div class="ingredient-item">{ingredient}</div>'
        for ingredient in recipe['ingredients']
    )
    ingredients_html += '</div></div>'
    
    instructions_html = '<div class="instructions-section">'
    instructions_html += '<h2>Instructions</h2>'
    for i, instruction in enumerate(recipe['instructions']):
        instructions_html += (
            f'<div class="instruction-step">'
            f'<div class="step-number">{i+1}</div>'
            f'<div>{instruction}</div>'
            '</div>'
        )
    instructions_html += '</div>'
    
    # Combine all sections
    complete_html = css + title_html + categories_html + info_html + ingredients_html + instructions_html
    
    return complete_html
