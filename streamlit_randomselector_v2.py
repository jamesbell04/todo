import random
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from collections import Counter
from datetime import datetime
from pathlib import Path
import html

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

    ingredient_counts = Counter(all_ingredients)

    shopping_lines = []

    for ingredient, count in sorted(ingredient_counts.items()):
        if count > 1:
            shopping_lines.append(f"{ingredient} ({count})")
        else:
            shopping_lines.append(ingredient)

    shopping_text = "\n".join(shopping_lines)

    st.text_area(
        "Copy/Paste",
        shopping_text,
        height=200,
    )

    # ---------------- Download HTML Shopping List ----------------

    now = datetime.now()
    timestamp_display = now.strftime("%Y-%m-%d %H:%M")
    timestamp_file = now.strftime("%Y-%m-%d_%H-%M")

    filename = f"shopping_list_{timestamp_file}.html"

    html_items = ""

    for item in shopping_lines:
        safe_item = html.escape(item)

        html_items += f"""
        <label class="item">
            <input type="checkbox">
            <span>{safe_item}</span>
        </label>
        """

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Shopping List</title>

<style>
body {{
    font-family: Arial, sans-serif;
    max-width: 900px;
    margin: auto;
    padding: 20px;
    font-size: 30px;
    line-height: 1.6;
    background: #fafafa;
}}

h1 {{
    font-size: 54px;
    margin: 0 0 10px 0;
}}

.date {{
    color: #666;
    font-size: 24px;
    margin-bottom: 25px;
}}

.item {{
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 20px;
    margin-bottom: 10px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.12);
}}

input[type="checkbox"] {{
    width: 46px;
    height: 46px;
    flex-shrink: 0;
}}

span {{
    flex: 1;
    font-size: 36px;
    word-break: break-word;
}}

input[type="checkbox"]:checked + span {{
    text-decoration: line-through;
    color: #888;
}}

.item:has(input[type="checkbox"]:checked) {{
    background: #dff5df;
}}
</style>
</head>

<body>

<h1>Shopping List</h1>

<div class="date">
Created: {timestamp_display}
</div>

{html_items}

</body>
</html>
"""

    st.download_button(
        "🛒 Download Interactive Shopping List",
        data=html_content,
        file_name=filename,
        mime="text/html",
    )
