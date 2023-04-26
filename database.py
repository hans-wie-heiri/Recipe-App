
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
from deta import Deta
from dotenv import load_dotenv
import pandas as pd
import nltk

# load the environment variables from the .env file in the directory (here the project key to the database)
#load_dotenv(".env")
DETA_KEY = st.secrets["DB_KEY"]


# Initialize with a project key
deta = Deta(DETA_KEY)

# this is how to create / connect a database
db1 = deta.Base("recipes")
db2 = deta.Base("recipe_ingredients")

# function that returns the reportentries on a successful creation, otherwise raises an error
def insert_recipe(name, recipe_id, description, tags):
    return db1.put({"key": name, "recipe_id": recipe_id, "description": description, "tags": tags})

# function that returns the reportentries on a successful creation, otherwise raises an error
def insert_recipe_ingredients(df):
    for i in range(len(df)):
        db2.put({"key": df['unique_key'][i], 
                 'recipe_id' : int(df['recipe_id'][i]),
                 'ingredient_id' : int(df['ingredient_id'][i]),
                 'ingredient' : str(df['ingredient'][i]),
                 'amount' : str(df['amount'][i]),
                 'unit' : str(df['unit'][i])
                            })

# function that fethes all names as a dictionary
def fetch_all_recipes():
    res = db1.fetch()
    return res.items

# function that gets period names
def get_all_recipes_names():
    items = fetch_all_recipes()
    names = [i["key"] for i in items]
    return names

# fetch name for plot - error will return none
def get_recipe_data(name):
    return db1.get(name)

def get_recipe_ingredients(recipe_id):
    res = db2.fetch({'recipe_id' : recipe_id})
    ingredients = []
    amounts = []
    units = []
    ingredient_id = []
    for i in res.items:
        amounts.append(i['amount'])
        ingredients.append(i['ingredient'])
        units.append(i['unit'])
        ingredient_id.append(i['ingredient_id'])
        
    ingredients_dict = {
        'ingredients': ingredients,
        'amounts' : amounts,
        'units' : units,
        'id' : ingredient_id
    }

    ingredient_df = pd.DataFrame(ingredients_dict)
    ingredient_df = ingredient_df.sort_values('id').reset_index(drop=True).drop('id', axis = 1)

    return ingredient_df


def get_all_ingredients():
    res = db2.fetch()
    ingredients = []
    for i in res.items:
        if i['ingredient'] not in ingredients:
            ingredients.append(i['ingredient'])
    return ingredients

def get_names_tags():
    res = db1.fetch()
    tags = []
    names = []
    recipe_ids = []
    tk_word = nltk.RegexpTokenizer(r'\s+', gaps=True)
    for recipe in res.items:
        tokenized_tags = tk_word.tokenize(recipe['tags'])
        name = recipe['key']
        recipe_id = recipe['recipe_id']
        for tag in tokenized_tags:
            if len(tag) > 1:
                tags.append(tag.lower())
                names.append(name)
                recipe_ids.append(recipe_id)
            
    name_tag_dict = {
        'name' : names,
        'tag' : tags,
        'recipe_id' : recipe_ids
    }

    name_tag_df = pd.DataFrame(name_tag_dict)
    
    return name_tag_df

def get_recipeId_ingredients():
    res = db2.fetch()
    recipe_ids = []
    ingredients = []
    for i in res.items:
        recipe_ids.append(i['recipe_id'])
        ingredients.append(i['ingredient'])
        
    recipe_ingredient_dict = {
        'recipe_id' : recipe_ids,
        'ingredient' : ingredients
    }
    
    recipe_ingredient_df = pd.DataFrame(recipe_ingredient_dict)
    
    return recipe_ingredient_df