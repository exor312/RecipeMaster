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
    }
    @media (max-width: 768px) {
        .recipe-grid {
            grid-template-columns: 1fr !important;
        }
    }
    .recipe-card {
        height: 100%;
        min-height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 1.5rem;
        margin: 0;
        border-radius: 5px;
        background-color: #f0f2f6;
    }
    .recipe-header {
        flex-grow: 1;
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
    .favorite-button {
        color: #ff4b4b;
        font-size: 1.5rem;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .favorite-button:hover {
        transform: scale(1.1);
    }
    .favorite-button.active {
        color: #ff0000;
    }
    .pagination {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem 0;
    }
    .recipe-details {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin-top: 1rem;
    }
    .back-button {
        margin-bottom: 1rem;
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

# Sidebar filters (only show when not viewing recipe details)
if st.session_state.viewing_recipe is None:
    st.sidebar.title("Recipe Filters")
    
    # Search box
    search_term = st.sidebar.text_input("Search recipes", "")
    
    # Cuisine filter
    if not st.session_state.recipes_df.empty:
        cuisines = ["All"] + sorted(st.session_state.recipes_df['cuisine'].unique().tolist())
        selected_cuisine = st.sidebar.selectbox("Select Cuisine", cuisines)
    
        # Category filter
        all_categories = set()
        for categories in st.session_state.recipes_df['categories']:
            all_categories.update(categories)
        categories_list = ["All"] + sorted(list(all_categories))
        selected_category = st.sidebar.selectbox("Select Category", categories_list)
    
        # Favorites filter
        show_favorites = st.sidebar.checkbox("Show Favorites Only")
        if show_favorites:
            st.sidebar.markdown(f"💝 **{len(st.session_state.favorites)} recipes** in favorites")
    else:
        selected_cuisine = None
        selected_category = None
        show_favorites = False

    # Apply filters
    filtered_recipes, total_pages = filter_recipes(
        st.session_state.recipes_df,
        search_term,
        selected_cuisine,
        selected_category,
        show_favorites,
        st.session_state.favorites,
        st.session_state.page_number
    )

# Recipe detail view
if st.session_state.viewing_recipe is not None:
    # Back button
    if st.button("← Back to Recipes", key="back_button", type="primary"):
        st.session_state.viewing_recipe = None
        st.rerun()
    
    recipe = st.session_state.viewing_recipe
    st.markdown("---")
    
    # Recipe details
    with st.container():
        # Show favorite button in details view
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"## {recipe['name']}")
        with col2:
            is_favorite = recipe['id'] in st.session_state.favorites
            favorite_icon = "★" if is_favorite else "☆"
            if st.button(favorite_icon, key=f"fav_detail_{recipe['id']}", help="Add/Remove from favorites"):
                if recipe['id'] in st.session_state.favorites:
                    st.session_state.favorites.remove(recipe['id'])
                    st.toast("Removed from favorites!", icon="✖️")
                else:
                    st.session_state.favorites.add(recipe['id'])
                    st.toast("Added to favorites!", icon="⭐")
                time.sleep(0.1)
                st.rerun()
        
        recipe_dict = recipe.to_dict()
        st.markdown(format_recipe_details(recipe_dict))

# Recipe grid view
elif 'filtered_recipes' in locals() and filtered_recipes.empty:
    if search_term or (selected_cuisine and selected_cuisine != "All") or (selected_category and selected_category != "All") or show_favorites:
        st.warning("No recipes found matching your criteria.")
    else:
        st.info("No recipes available. Please add some recipes to get started.")
else:
    # Display recipes in a grid
    st.markdown('<div class="recipe-grid">', unsafe_allow_html=True)
    
    for _, recipe in filtered_recipes.iterrows():
        # Create category tags HTML
        category_tags = ''.join([f'<span class="category-tag">{cat}</span>' for cat in recipe['categories']])
        
        # Favorite button with active state
        is_favorite = recipe['id'] in st.session_state.favorites
        favorite_icon = "★" if is_favorite else "☆"
        
        st.markdown(f"""
            <div class="recipe-card">
                <div class="recipe-header">
                    <h3>{recipe['name']}</h3>
                    <p>Cuisine: {recipe['cuisine']} | {recipe['difficulty']}</p>
                    <p>{category_tags}</p>
                </div>
                <div class="recipe-actions">
                    <div>
                        <!-- View Details button will be placed here -->
                    </div>
                    <div>
                        <!-- Favorite button will be placed here -->
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Add interactive buttons
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(f"View Details", key=f"view_{recipe['id']}"):
                st.session_state.viewing_recipe = recipe
                st.rerun()
        
        with col2:
            if st.button(f"{favorite_icon}", key=f"fav_{recipe['id']}", help="Add/Remove from favorites"):
                if recipe['id'] in st.session_state.favorites:
                    st.session_state.favorites.remove(recipe['id'])
                    st.toast("Removed from favorites!", icon="✖️")
                else:
                    st.session_state.favorites.add(recipe['id'])
                    st.toast("Added to favorites!", icon="⭐")
                time.sleep(0.1)
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Pagination (only show in grid view)
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
st.markdown("Browse through our collection of delicious recipes. Use the sidebar to filter by cuisine and category!")
