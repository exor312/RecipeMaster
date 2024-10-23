import streamlit as st
import pandas as pd
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
    .recipe-card {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .recipe-header {
        margin-bottom: 1rem;
    }
    .recipe-actions {
        display: grid;
        grid-template-columns: 3fr 1fr;
        gap: 1rem;
        align-items: center;
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
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin: 1rem 0;
    }
    .loading-container {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
        z-index: 1000;
    }
    .loading-spinner {
        width: 50px;
        height: 50px;
        border: 5px solid #f3f3f3;
        border-top: 5px solid #FF4B4B;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page_number' not in st.session_state:
    st.session_state.page_number = 1

if 'favorites' not in st.session_state:
    st.session_state.favorites = set()

# Custom loading indicator
def show_loading(message="Loading..."):
    st.markdown(f"""
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <p>{message}</p>
        </div>
    """, unsafe_allow_html=True)

# Load recipes
if 'recipes_df' not in st.session_state:
    show_loading('Loading recipes...')
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

# Sidebar filters
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

# Main content
st.title("🍳 Recipe Browser")

if filtered_recipes.empty:
    if search_term or (selected_cuisine and selected_cuisine != "All") or (selected_category and selected_category != "All") or show_favorites:
        st.warning("No recipes found matching your criteria.")
    else:
        st.info("No recipes available. Please add some recipes to get started.")
else:
    # Display recipes in a grid
    cols = st.columns(2)
    for idx, (_, recipe) in enumerate(filtered_recipes.iterrows()):
        with cols[idx % 2]:
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
                    show_loading("Loading recipe details...")
                    st.markdown("---")
                    st.markdown(format_recipe_details(recipe))
                    
                    # Recipe metadata using CSS Grid
                    st.markdown(f"""
                        <div class="recipe-details">
                            <div>
                                <strong>Preparation Time:</strong> {recipe['preview_data']['prep_time']}
                            </div>
                            <div>
                                <strong>Cooking Time:</strong> {recipe['preview_data']['cook_time']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                if st.button(f"{favorite_icon}", key=f"fav_{recipe['id']}", help="Add to favorites", type="primary" if is_favorite else "secondary"):
                    if recipe['id'] in st.session_state.favorites:
                        st.session_state.favorites.remove(recipe['id'])
                        st.success(f"Removed '{recipe['name']}' from favorites!")
                    else:
                        st.session_state.favorites.add(recipe['id'])
                        st.success(f"Added '{recipe['name']}' to favorites!")
                    st.rerun()

    # Pagination
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
