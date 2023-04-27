
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

    def create_id():
        stamp= time.time()
        id = int(round(stamp * 100,0))
        return id

    def first_if_any(list):
        if len(list) == 0:
            return None
        else:
            return list[0]

    # ------------- Navigation Menu --------------

    selected = option_menu(
        menu_title = None,
        options=[ "Find Recipe", "Add Recipe"],
        icons=["search", "pencil-fill"],    # https://icons.getbootstrap.com/
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

            tk_line = LineTokenizer()
            imp_tokenized = tk_line.tokenize(ingredients_txt)

            tk_word = nltk.RegexpTokenizer(r'\s+', gaps=True)
            data = {
                'recipe_id' : [],
                'ingredient_id' : [],
                'ingredient' : [],
                'amount' : [],
                'unit' : []
            }
            df = pd.DataFrame(data)

            recipe_id = create_id()
            ingredient_id = 1

            for line in imp_tokenized:
                tokenized_line = tk_word.tokenize(line)
                ingredients = []
                amount = []
                unit = []
                for word in tokenized_line:
                    low_word = word.lower()
                    if low_word in unit_list:
                        unit.append(word)
                    else:
                        try:
                            result = float(word)
                            amount.append(result)
                        except ValueError:
                            ingredients.append(word)
                    ingredient_str = ' '.join(ingredients)
                
                new_row = {
                    'recipe_id' : recipe_id,
                    'ingredient_id' : ingredient_id,
                    'ingredient' : ingredient_str,
                    'amount' : first_if_any(amount),
                    'unit' : first_if_any(unit)
                }
                
                # Use the loc method to add the new row to the DataFrame
                df.loc[len(df)] = new_row
                
                ingredient_id += 1
                
            df['unique_key'] = df['recipe_id'].map(str) + df['ingredient_id'].map(str)
            df['amount'] = df['amount'].fillna(0)
            df['unit'] = df['unit'].fillna('keine')

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


    # ------------- Input and save recipes --------------
    if selected == "Find Recipe":
        st.header('Find a delicious Recipe')

        
        # user selction by ingredient
        us_ingredients = st.multiselect('Do you want to select specific ingredients?', recipe_ingredient_df['ingredient'].unique())

        if len(us_ingredients) > 0:
            ingredients_subset_df = recipe_ingredient_df[recipe_ingredient_df['ingredient'].isin(us_ingredients)]
            remaining_ids = ingredients_subset_df['recipe_id'].unique()
            name_tag_df = name_tag_df[name_tag_df['recipe_id'].isin(remaining_ids)]

        # user selction by tag
        us_tags = st.multiselect('Do you want to search specific tags?', name_tag_df['tag'].unique())
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

            # ingredients_list_onetext = db.create_ingredients_text(ingredients_df)

            # st.write(ingredients_list_onetext)