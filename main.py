import streamlit as st
import pandas as pd
import time
from utils import load_recipes, filter_recipes, format_recipe_details

# Page configuration
st.set_page_config(
    page_title="Recipe Browser",
    page_icon="🍳",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton > button {
        width: 100%;
    }
    .recipe-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 1.5rem;
        margin: 1rem 0;
        width: 100%;
    }
    @media (max-width: 768px) {
        .recipe-grid {
            grid-template-columns: 1fr !important;
        }
    }
    .recipe-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        width: 100%;
        box-sizing: border-box;
    }
    .recipe-header {
        margin-bottom: 1rem;
    }
    .recipe-actions {
        display: grid;
        grid-template-columns: 3fr 1fr;
        gap: 1rem;
        align-items: center;
        margin-top: 1rem;
    }
    .category-tag {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        margin: 0.2rem;
        border-radius: 15px;
        background-color: #e1e1e1;
        font-size: 0.8rem;
    }
    button[type="secondary"] {
        background-color: #FFD700 !important;
        border: none !important;
        padding: 0.5rem !important;
        font-size: 24px !important;
        color: black !important;
        border-radius: 4px !important;
        transition: transform 0.2s !important;
    }
    button[type="secondary"]:hover {
        background-color: #FFB400 !important;
        transform: scale(1.05) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page_number' not in st.session_state:
    st.session_state.page_number = 1

if 'favorites' not in st.session_state:
    st.session_state.favorites = set()

if 'viewing_recipe' not in st.session_state:
    st.session_state.viewing_recipe = None

if 'prev_show_favorites' not in st.session_state:
    st.session_state.prev_show_favorites = False

# Load recipes
if 'recipes_df' not in st.session_state:
    with st.spinner('Loading recipes...'):
        try:
            st.session_state.recipes_df = load_recipes()
        except FileNotFoundError as e:
            st.error(str(e))
            st.info("Please add recipe JSON files to the 'data/recipe' directory to get started.")
            st.stop()
        except ValueError as e:
            st.error(str(e))
            st.info("Please ensure your recipe JSON files contain all required fields.")
            st.stop()
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            st.stop()

# Main title
st.title("🍳 Recipe Browser")

# Recipe detail view
if st.session_state.viewing_recipe is not None:
    recipe = st.session_state.viewing_recipe
    
    # Back and favorite buttons
    col1, col2 = st.columns([4, 1])
    
    with col1:
        if st.button("← Back to Recipes", type="primary"):
            st.session_state.viewing_recipe = None
            st.rerun()
    
    with col2:
        is_favorite = recipe['id'] in st.session_state.favorites
        favorite_icon = "★" if is_favorite else "☆"
        if st.button(favorite_icon, key="detail_favorite", help="Add/Remove from favorites", type="secondary"):
            if recipe['id'] in st.session_state.favorites:
                st.session_state.favorites.remove(recipe['id'])
                message = "Removed from favorites!"
                icon = "✖️"
            else:
                st.session_state.favorites.add(recipe['id'])
                message = "Added to favorites!"
                icon = "⭐"
            st.toast(message, icon=icon)
            time.sleep(1.5)
            st.rerun()
    
    st.markdown("---")
    
    # Recipe details
    recipe_dict = recipe.to_dict() if isinstance(recipe, pd.Series) else recipe
    st.markdown(format_recipe_details(recipe_dict), unsafe_allow_html=True)

else:
    # Sidebar filters
    st.sidebar.title("Recipe Filters")
    
    # Search box
    search_term = st.sidebar.text_input("Search recipes", "")
    
    # Difficulty filter
    if not st.session_state.recipes_df.empty:
        difficulties = ["All"] + sorted(st.session_state.recipes_df['difficulty'].unique().tolist())
        selected_difficulty = st.sidebar.selectbox("Select Difficulty", difficulties)
    
        # Category filter
        all_categories = set()
        for categories in st.session_state.recipes_df['categories']:
            all_categories.update(categories)
        categories_list = ["All"] + sorted(list(all_categories))
        selected_category = st.sidebar.selectbox("Select Category", categories_list)
    
        # Favorites filter
        show_favorites = st.sidebar.checkbox("Show Favorites Only")
        
        # Reset page number when toggling favorites
        if show_favorites != st.session_state.prev_show_favorites:
            st.session_state.page_number = 1
            st.session_state.prev_show_favorites = show_favorites
        
        # Update favorites count display
        if show_favorites:
            total_favorites = len([r for _, r in st.session_state.recipes_df.iterrows() 
                                 if r['id'] in st.session_state.favorites])
            st.sidebar.markdown(f"💝 **{total_favorites} recipes** in favorites")
    else:
        selected_difficulty = None
        selected_category = None
        show_favorites = False

    # Apply filters
    filtered_recipes, total_pages = filter_recipes(
        st.session_state.recipes_df,
        search_term,
        selected_difficulty,
        selected_category,
        show_favorites,
        st.session_state.favorites,
        st.session_state.page_number,
        per_page=10  # Limit to 10 items per page
    )

    # Recipe grid view
    if not st.session_state.recipes_df.empty and (
        'filtered_recipes' not in locals() or filtered_recipes.empty
    ):
        if search_term or (selected_difficulty and selected_difficulty != "All") or (selected_category and selected_category != "All") or show_favorites:
            st.warning("No recipes found matching your criteria.")
        else:
            st.info("No recipes available. Please add some recipes to get started.")
    else:
        # Display recipes in a grid using columns
        for i in range(0, len(filtered_recipes), 2):
            col1, col2 = st.columns(2)
            
            # First recipe in the pair
            with col1:
                recipe = filtered_recipes.iloc[i]
                category_tags = ''.join([f'<span class="category-tag">{cat}</span>' for cat in recipe['categories']])
                is_favorite = recipe['id'] in st.session_state.favorites
                favorite_icon = "★" if is_favorite else "☆"
                
                st.markdown(f"""
                    <div class="recipe-card">
                        <div class="recipe-header">
                            <h3>{recipe['name']}</h3>
                            <p>⏱️ {recipe['preview_data']['cook_time']} | 📊 {recipe['difficulty']}</p>
                            <p>{category_tags}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                view_col1, fav_col1 = st.columns([3, 1])
                with view_col1:
                    if st.button("View Details", key=f"view_{recipe['id']}_1"):
                        st.session_state.viewing_recipe = recipe
                        st.rerun()
                with fav_col1:
                    if st.button(favorite_icon, key=f"fav_{recipe['id']}_1", help="Add/Remove from favorites", type="secondary"):
                        if recipe['id'] in st.session_state.favorites:
                            st.session_state.favorites.remove(recipe['id'])
                            message = "Removed from favorites!"
                            icon = "✖️"
                        else:
                            st.session_state.favorites.add(recipe['id'])
                            message = "Added to favorites!"
                            icon = "⭐"
                        st.toast(message, icon=icon)
                        time.sleep(1.5)
                        st.rerun()
            
            # Second recipe in the pair (if available)
            if i + 1 < len(filtered_recipes):
                with col2:
                    recipe = filtered_recipes.iloc[i + 1]
                    category_tags = ''.join([f'<span class="category-tag">{cat}</span>' for cat in recipe['categories']])
                    is_favorite = recipe['id'] in st.session_state.favorites
                    favorite_icon = "★" if is_favorite else "☆"
                    
                    st.markdown(f"""
                        <div class="recipe-card">
                            <div class="recipe-header">
                                <h3>{recipe['name']}</h3>
                                <p>⏱️ {recipe['preview_data']['cook_time']} | 📊 {recipe['difficulty']}</p>
                                <p>{category_tags}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    view_col2, fav_col2 = st.columns([3, 1])
                    with view_col2:
                        if st.button("View Details", key=f"view_{recipe['id']}_2"):
                            st.session_state.viewing_recipe = recipe
                            st.rerun()
                    with fav_col2:
                        if st.button(favorite_icon, key=f"fav_{recipe['id']}_2", help="Add/Remove from favorites", type="secondary"):
                            if recipe['id'] in st.session_state.favorites:
                                st.session_state.favorites.remove(recipe['id'])
                                message = "Removed from favorites!"
                                icon = "✖️"
                            else:
                                st.session_state.favorites.add(recipe['id'])
                                message = "Added to favorites!"
                                icon = "⭐"
                            st.toast(message, icon=icon)
                            time.sleep(1.5)
                            st.rerun()

        # Pagination
        if total_pages > 1:
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.session_state.page_number > 1:
                    if st.button("← Previous"):
                        st.session_state.page_number -= 1
                        st.rerun()
                        
            with col2:
                st.markdown(f"<div style='text-align: center'>Page {st.session_state.page_number} of {total_pages}</div>", unsafe_allow_html=True)
                
            with col3:
                if st.session_state.page_number < total_pages:
                    if st.button("Next →"):
                        st.session_state.page_number += 1
                        st.rerun()

# Footer
st.markdown("---")
st.markdown("### 📖 Recipe Browser App")
st.markdown("Browse through our collection of delicious recipes. Use the sidebar to filter by difficulty and category!")
