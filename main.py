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
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'recipes_df' not in st.session_state:
    try:
        st.session_state.recipes_df = load_recipes()  # Using default 'data/recipe' directory
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
else:
    selected_cuisine = None

# Apply filters
filtered_recipes = filter_recipes(
    st.session_state.recipes_df,
    search_term,
    selected_cuisine
)

# Main content
st.title("🍳 Recipe Browser")

if filtered_recipes.empty:
    if search_term or (selected_cuisine and selected_cuisine != "All"):
        st.warning("No recipes found matching your criteria.")
    else:
        st.info("No recipes available. Please add some recipes to get started.")
else:
    # Display recipes in a grid
    cols = st.columns(2)
    for idx, (_, recipe) in enumerate(filtered_recipes.iterrows()):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"""
                    <div class="recipe-card">
                        <h3>{recipe['name']}</h3>
                        <p>Cuisine: {recipe['difficulty']} | {recipe['cuisine']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"View Details", key=f"btn_{recipe['id']}"):
                    st.markdown("---")
                    st.markdown(format_recipe_details(recipe))
                    
                    # Additional recipe metadata
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Preparation Time", recipe['prep_time'])
                    with col2:
                        st.metric("Cooking Time", recipe['cook_time'])

# Footer
st.markdown("---")
st.markdown("### 📖 Recipe Browser App")
st.markdown("Browse through our collection of delicious recipes. Use the sidebar to filter and search!")
