import random
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

# ---------------- Settings ----------------

SHEET_ID = "1bGdjwslq5R59sXSwrAmjlYsRJwNIAx37dReGIk6WSIM"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

# ---------------- Connect to Google Sheet ----------------

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)

gc = gspread.authorize(creds)

sheet = gc.open_by_key(SHEET_ID)
worksheet = sheet.sheet1

rows = worksheet.get_all_records()

# ---------------- Clean column names ----------------
# This fixes problems like:
# Meal vs meal
# Ingredient 1 vs ingredient 1
# extra spaces in headers

clean_rows = []

for row in rows:
    clean_row = {}

    for key, value in row.items():
        clean_key = str(key).strip().lower()
        clean_row[clean_key] = value

    clean_rows.append(clean_row)

# ---------------- Streamlit App ----------------

import pandas as pd

st.title("🍽️ Random Meal Picker")

num_meals = st.number_input(
    "Number of meals",
    min_value=1,
    max_value=min(10, len(clean_rows)),
    value=3,
)

if st.button("🎲 Generate Meals"):
    st.session_state["selected_meals"] = random.sample(clean_rows, num_meals)

if "selected_meals" in st.session_state:

    selected_meals = st.session_state["selected_meals"]

    table = {}
    all_ingredients = []

    # ---------------- Create table ----------------

    for meal in selected_meals:

        ingredients = []

        for i in range(1, 11):

            ingredient = meal.get(f"i{i}", "")

            if str(ingredient).strip():

                ingredient = str(ingredient).strip()

                ingredients.append(ingredient)
                all_ingredients.append(ingredient)

        table[meal["meal"]] = [
            meal.get("class", ""),
            meal.get("source", ""),
            "\n".join(ingredients)
        ]

    df = pd.DataFrame(
        table,
        index=[
            "Class",
            "Source",
            "Ingredients"
        ]
    )

    st.header("Selected Meals")

    cols = st.columns(len(selected_meals))

    all_ingredients = []

    for col, meal in zip(cols, selected_meals):

        ingredients = []

        for i in range(1, 11):
            ingredient = meal.get(f"i{i}", "")

            if str(ingredient).strip():
                ingredient = str(ingredient).strip()
                ingredients.append(ingredient)
                all_ingredients.append(ingredient)

        with col:

            st.markdown(f"### **{meal['meal']}**")

            st.markdown(f"**Class:** {meal.get('class','')}")

            if meal.get("source",""):
                st.markdown(f"**Source:** {meal['source']}")

            st.markdown("**Ingredients**")

            for ingredient in ingredients:
                st.markdown(f"• **{ingredient}**")

    # ---------------- Shopping list ----------------

    st.header("Shopping List")

    shopping = sorted(set(all_ingredients))

    shopping_text = "\n".join(shopping)

    st.text_area(
        "Copy/Paste",
        shopping_text,
        height=250,
    )
