
# ------------- Linbraries --------------
import os
import calendar
from datetime import datetime
import pandas as pd
from nltk.tokenize import LineTokenizer
import nltk
import time
import streamlit as st
from streamlit_option_menu import option_menu 
import plotly.graph_objects as go
import plotly.express as px

import database as db

# ------------- start app if password is correct --------------
if db.check_password():

    # ------------- Settings --------------

    page_title = "Cathy's & Lori's Recepies"
    page_icon = ':spaghetti:' # emoji : https://www.webfx.com/tools/emoji-cheat-sheet/
    layout = 'centered' # derfault but can be chenged to wide

    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
    st.title(page_title + " " + page_icon)

    # ------------- hide streamlit style --------------

    hide_st_style = """
    <style>

    footer {visibility: hidden;}
    </style>
    """

    # #MainMenu {visibility: hidden;} this would be another option (inkl.# )

    st.markdown(hide_st_style, unsafe_allow_html=True)

    # ------------- Load data from base --------------

    name_tag_df = db.get_names_tags()
    recipe_ingredient_df = db.get_recipeId_ingredients()


    # ------------- Unit look up table --------------

    units = pd.read_csv('lookup_tab/units_raw.csv', encoding='latin-1', sep = ",", engine='python')
    unit_list = list(units['Name'])

    # ------------- Helper Functions --------------

   

    # ------------- Navigation Menu --------------

    selected = option_menu(
        menu_title = None,
        options=[ "Find Recipe", "Add Recipe", "shopping list"],
        icons=["search", "pencil-fill", "cart4"],    # https://icons.getbootstrap.com/
        orientation="horizontal"
    )

    # ------------- Input and save recipes --------------
    if selected == "Add Recipe":
        st.header('Add Recipe')
        st.write('To change an existing recipe, just enter the name. Make sure the spelling matches.')

        recipe_name = st.text_input('Insert the Recipe Name')
        update_recipe = recipe_name in name_tag_df['name'].unique() # returns true if name allready exists

        # if the recipe already exists it will be update
        if update_recipe:
            st.warning('There is allready a recipe with this name. The previous recipe will be overwritten.', icon="⚠️")

            update_recipe_name = st.text_input('Insert the New Recipe Name', recipe_name)

            update_recipe_data = db.get_recipe_data(recipe_name)    # comes from selectbox above
            update_description = update_recipe_data.get("description")
            update_recipe_id = update_recipe_data.get("recipe_id")
            update_recipe_tags = update_recipe_data.get("tags")
            
            update_ingredients_df = db.get_recipe_ingredients(update_recipe_id)

            update_ingredients = db.create_ingredients_text(update_ingredients_df)
        else:
            update_ingredients = """"""
            update_description = """"""
            update_recipe_tags = ""
            update_recipe_name = recipe_name

        ingredients_txt = st.text_area("Insert Recipe Ingredients (with a line break)", update_ingredients,  height = 250)

        if "extraction_state" not in st.session_state :
            st.session_state.extraction_state = False

        if len(ingredients_txt) > 0:
        #     extraction = st.button('start')
        # else:
        #     extraction = False

        # if extraction or st.session_state.extraction_state:
        #     st.session_state.extraction_state = True

            df = db.ingredients_txt_to_df(ingredients_txt, unit_list)

            recipe_id = max(df['recipe_id'])

            st.write("That's how it will be saved:")
            st.dataframe(df[['ingredient', 'amount', 'unit']])

        description_txt = st.text_area("Insert Recipe Description", update_description,  height = 250)

        tags_txt = st.text_input("Insert Tags", update_recipe_tags)

        if len(update_recipe_name) > 0 and len(ingredients_txt) > 0 and len(df) > 0 and len(description_txt) > 0:
            submitted = st.button('Save Recipe')
            if submitted:
                if update_recipe:
                    db.delete_recipe(recipe_name)
                    db.delete_recipe_ingredients(update_ingredients_df)
                db.insert_recipe(update_recipe_name, recipe_id, description_txt, tags_txt)
                db.insert_recipe_ingredients(df)
                st.success("Data saved!")


    # ------------- Find recipes --------------
    if selected == "Find Recipe":
        st.header('Find a delicious Recipe')

        
        # user selction by ingredient
        us_ingredients = st.multiselect('Do you want to select specific ingredients?', sorted(recipe_ingredient_df['ingredient'].unique()))

        if len(us_ingredients) > 0:
            ingredients_subset_df = recipe_ingredient_df[recipe_ingredient_df['ingredient'].isin(us_ingredients)]
            remaining_ids = ingredients_subset_df['recipe_id'].unique()
            name_tag_df = name_tag_df[name_tag_df['recipe_id'].isin(remaining_ids)]

        # user selction by tag
        us_tags = st.multiselect('Do you want to search specific tags?', sorted(name_tag_df['tag'].unique()))
        if len(us_tags) > 0:
            tag_subset_df = name_tag_df[name_tag_df['tag'].isin(us_tags)]
        else: 
            tag_subset_df = name_tag_df



        # tabel after tag end ingredient selection

        
        st.info('There are ' + str(len(tag_subset_df['name'].unique())) + ' recipes to select from.', icon="ℹ️")

        recipe_name = st.selectbox('Select a Recipe', tag_subset_df['name'].unique())
        recipe_data = db.get_recipe_data(recipe_name)    # comes from selectbox above
        description = recipe_data.get("description")
        recipe_id = recipe_data.get("recipe_id")
        recipe_tags = recipe_data.get("tags")
        
        st.markdown("""---""")

        st.header(recipe_name)

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader('Recipe')
            st.write(description)

        with col2:
            st.subheader('Ingredients')
            ingredients_df = db.get_recipe_ingredients(recipe_id)

            for i in range(len(ingredients_df)):
                if ingredients_df['amounts'][i] == '0.0':
                    amount_char = ''
                else:
                    amount_char = str(ingredients_df['amounts'][i])

                if ingredients_df['units'][i] == 'keine':
                    unit_char = ''
                else:
                    unit_char = str(ingredients_df['units'][i])

                st.write(ingredients_df['ingredients'][i] + ' ' + amount_char + ' ' + unit_char)

        st.write('Tags: ' + recipe_tags)

            # ingredients_list_onetext = db.create_ingredients_text(ingredients_df)

            # st.write(ingredients_list_onetext)

    # -------------create shopping list --------------
    if selected == "shopping list":
        st.header('shopping list')

        receipes_shopping = st.multiselect('Select some Recipes', sorted(name_tag_df['name'].unique()))
        
        if len(receipes_shopping) > 0:
            subset_recipes_shopping = name_tag_df[name_tag_df['name'].isin(receipes_shopping)]

            recipe_shopping_ids = list(subset_recipes_shopping['recipe_id'].unique())

            all_ingredients_df = pd.DataFrame( {
                'ingredients': [],
                'amounts' : [],
                'units' : [],
                'ingredients_keys' : []
            })

            for recipe_id in (recipe_shopping_ids):
                ingredients_df = db.get_recipe_ingredients(int(recipe_id))
                all_ingredients_df = pd.concat([all_ingredients_df, ingredients_df])
            all_ingredients_df['amounts'] = pd.to_numeric(all_ingredients_df['amounts'])

            shopping_list_df = pd.DataFrame(all_ingredients_df.groupby(['ingredients', 'units'])['amounts'].sum())
            shopping_list_df = shopping_list_df.reset_index()
            shopping_list_df = shopping_list_df[['ingredients', 'amounts', 'units']]
            shopping_list_df = shopping_list_df[shopping_list_df['amounts'] > 0]
            shopping_list_df = shopping_list_df.reset_index(drop=True)

            edit_shopping_list = db.create_ingredients_text(shopping_list_df)

            shopping_ingredients_txt = st.text_area("Insert Shopping Ingredients (with a line break)", edit_shopping_list,  height = 250)

            shopping_df_for_print = db.ingredients_txt_to_df(shopping_ingredients_txt, unit_list)
            shopping_df_for_print = shopping_df_for_print[['ingredient', 'amount', 'unit']]

            with st.expander("See shopping list preview"):
                st.dataframe(shopping_df_for_print)

            @st.cache_data
            def convert_df(df):
                return df.style.format({"amount": "{:.2f}"}).to_html().encode('utf-8')

            html = convert_df(shopping_df_for_print)

            st.download_button(
                "Download Shopping List",
                html,
                "shopping_list.html"
            )