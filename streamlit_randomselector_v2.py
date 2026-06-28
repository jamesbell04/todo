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

st.title("🍽️ Random Meal Picker")


if st.button("🎲 Pick Random Meal"):
    st.session_state["selected_meal"] = random.choice(clean_rows)

if "selected_meal" in st.session_state:

    meal = st.session_state["selected_meal"]

    meal_name = meal.get("meal", "No meal name found")
    meal_class = meal.get("class", "")
    meal_source = meal.get("source", "")

    st.header(meal_name)

    st.write(f"**Class:** {meal_class}")
    st.write(f"**Source:** {meal_source}")

    st.subheader("Ingredients")

    ingredients = []

    for column, value in meal.items():
        if column.startswith("ingredient"):
            if str(value).strip() != "":
                ingredients.append(value)

    if len(ingredients) == 0:
        st.warning("No ingredients found for this meal.")
    else:
        for ingredient in ingredients:
            st.write(f"• {ingredient}")
