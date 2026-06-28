import random
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from collections import Counter
from datetime import datetime
from pathlib import Path
import html
import random
from collections import Counter

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
st.title("🍽️ What to Eat?")

num_meals = st.number_input(
    "Number of meals",
    min_value=1,
    max_value=min(10, len(clean_rows)),
    value=3,
)

# ---------------- Generate new full set ----------------

if st.button("🎲 Generate New Meals"):
    st.session_state["selected_meals"] = random.sample(clean_rows, num_meals)
    st.session_state["keep_flags"] = [False] * num_meals
    st.rerun()

if "selected_meals" in st.session_state:

    selected_meals = st.session_state["selected_meals"]

    # Ensure keep_flags exists and has correct length
    if "keep_flags" not in st.session_state:
        st.session_state["keep_flags"] = [False] * len(selected_meals)

    while len(st.session_state["keep_flags"]) < len(selected_meals):
        st.session_state["keep_flags"].append(False)

    if len(st.session_state["keep_flags"]) != len(selected_meals):
        st.session_state["keep_flags"] = [False] * len(selected_meals)

    
    # ---------------- Display meals ----------------

    st.header("Selected Meals")

    cols = st.columns(len(selected_meals))

    all_ingredients = []

    for i, (col, meal) in enumerate(zip(cols, selected_meals)):

        ingredients = []

        for j in range(1, 11):
            ingredient = meal.get(f"i{j}", "")

            if str(ingredient).strip():
                ingredient = str(ingredient).strip()
                ingredients.append(ingredient)
                all_ingredients.append(ingredient)

        with col:

            locked = st.checkbox(
                "Keep",
                value=st.session_state["keep_flags"][i],
                key=f"keep_{i}"
            )

            st.session_state["keep_flags"][i] = locked

            st.markdown(f"### **{meal.get('meal', 'Unknown meal')}**")
            st.markdown(f"**Class:** {meal.get('class', '')}")

            if meal.get("source", ""):
                st.markdown(f"**Source:** {meal.get('source', '')}")

            st.markdown("**Ingredients**")

            for ingredient in ingredients:
                st.markdown(f"• {ingredient}")

    # ---------------- Replace unlocked meals ----------------
    # ---------------- Replace unkept meals ----------------

    if st.button("🔁 Replace Unkept Meals"):

        new_selected_meals = []

        kept_names = {
            meal.get("meal")
            for meal, keep in zip(selected_meals, st.session_state["keep_flags"])
            if keep
        }

        current_names = {meal.get("meal") for meal in selected_meals}

        available_meals = [
            meal for meal in clean_rows
            if meal.get("meal") not in current_names
        ]

        for meal, keep in zip(selected_meals, st.session_state["keep_flags"]):

            if keep:
                new_selected_meals.append(meal)

            else:
                if not available_meals:
                    available_meals = [
                        meal for meal in clean_rows
                        if meal.get("meal") not in kept_names
                    ]

                new_meal = random.choice(available_meals)
                available_meals.remove(new_meal)
                new_selected_meals.append(new_meal)

        st.session_state["selected_meals"] = new_selected_meals

        # Kept meals stay checked, new ones start unchecked
        st.session_state["keep_flags"] = [
            keep for keep in st.session_state["keep_flags"]
        ]

        st.rerun()

    # ---------------- Shopping list ----------------

     

    st.header("Shopping List")

    ingredient_counts = Counter(all_ingredients)

    shopping_lines = []

    for ingredient, count in sorted(ingredient_counts.items()):
        if count > 1:
            shopping_lines.append(f"{ingredient} ({count})")
        else:
            shopping_lines.append(ingredient)

    # ---------------- Add manual shopping item ----------------

    if "manual_items" not in st.session_state:
        st.session_state["manual_items"] = []

    st.subheader("Add extra item")

    add_col1, add_col2 = st.columns([4, 1])

    with add_col1:
        extra_item = st.text_input(
            "Extra item",
            label_visibility="collapsed",
            placeholder="e.g. Milk",
            key="extra_item_input",
        )

    with add_col2:
        add_clicked = st.button("➕ Add")

    if add_clicked:
        extra_item = extra_item.strip()

        if extra_item:
            st.session_state["manual_items"].append(extra_item)
            st.rerun()

    for item in st.session_state["manual_items"]:
        shopping_lines.append(item)

    shopping_lines = sorted(shopping_lines)

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

    meal_list_html = ""

    for meal in selected_meals:
        safe_meal_name = html.escape(meal.get("meal", "Unknown meal"))
        meal_list_html += f"<li><strong>{safe_meal_name}</strong></li>"

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
    padding: 16px;
    font-size: 24px;
    line-height: 1.45;
    background: #fafafa;
}}

h1 {{
    font-size: 36px;
    margin: 0 0 8px 0;
}}

h2 {{
    font-size: 26px;
    margin-top: 24px;
    margin-bottom: 8px;
}}

.date {{
    color: #666;
    font-size: 20px;
    margin-bottom: 20px;
}}

.meals {{
    font-size: 22px;
    line-height: 1.4;
    margin-bottom: 20px;
}}

.meals li {{
    margin-bottom: 6px;
}}

.item {{
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    margin-bottom: 8px;
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.10);
}}

input[type="checkbox"] {{
    width: 28px;
    height: 28px;
    flex-shrink: 0;
}}

span {{
    flex: 1;
    font-size: 21px;
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

<h2>Meals</h2>
<ul class="meals">
{meal_list_html}
</ul>

<h2>Ingredients</h2>

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
