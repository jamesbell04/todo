import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------------- Google Sheets access ----------------

SHEET_ID = "1bGdjwslq5R59sXSwrAmjlYsRJwNIAx37dReGIk6WSIM"
WORKSHEET_NAME = "Sheet2"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES,
)

gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID)
worksheet = sheet.worksheet(WORKSHEET_NAME)

# ---------------- Sheet layout ----------------

ROW_DATE = 1
ROW_JOBS = 2
ROW_SCHEDULE = 3
ROW_STATUS = 4
ROW_CALC = 5
ROW_LAST = 6

# ---------------- Load data ----------------

data = worksheet.get_all_values()

jobs = data[ROW_JOBS - 1][1:]
schedules = data[ROW_SCHEDULE - 1][1:]
last_dates = data[ROW_LAST - 1][1:]

today = datetime.now().date()
today_text = today.strftime("%d/%m/%Y")

# Update date in A1
worksheet.update_cell(ROW_DATE, 1, today_text)

# ---------------- Streamlit app ----------------

st.title("🧹 Job Tracker")
st.write(f"Today: **{today_text}**")

for i, job in enumerate(jobs):

    if not job.strip():
        continue

    col_number = i + 2  # B = 2, C = 3, etc.

    schedule_days = float(schedules[i])
    last_text = last_dates[i].strip()

    if last_text:
        last_date = datetime.strptime(last_text, "%d/%m/%Y").date()
        days_since = (today - last_date).days
    else:
        days_since = 9999

    status = "Due" if days_since > schedule_days else "OK"

    # Update Status and Calc rows in Google Sheet
    worksheet.update_cell(ROW_STATUS, col_number, status)
    worksheet.update_cell(ROW_CALC, col_number, days_since)

    st.subheader(job)

    col1, col2, col3, col4 = st.columns([1.2, 1.8, 1.8, 1])

    with col1:
        if status == "Due":
            st.error("Due")
        else:
            st.success("OK")

    with col2:
        st.write(f"**Last:** {last_text if last_text else 'Never'}")

    with col3:
        st.write(f"**Days Since:** {days_since}")
        st.write(f"**Schedule:** {schedule_days:g} days")

    with col4:
        done = st.checkbox("Done", key=f"done_{job}")

    if done:
        worksheet.update_cell(ROW_LAST, col_number, today_text)
        worksheet.update_cell(ROW_CALC, col_number, 0)
        worksheet.update_cell(ROW_STATUS, col_number, "OK")

        st.success(f"{job} updated to {today_text}")
        st.rerun()

    st.divider()