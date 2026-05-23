"""Step 2: Read a public Google Sheet and build a dashboard.

The sheet is "published to the web" as CSV — anyone with the URL can read it.
No authentication, no secrets, no API keys. We load it with pandas and
visualise with Streamlit's built-in charts.

To use your own sheet:
  1. Follow docs/02-publish-sheet-to-web.md to publish a sheet as CSV.
  2. Replace SHEET_CSV_URL below with your URL.
  3. Commit on github.com — Streamlit Cloud will auto-redeploy.

Expected columns (header row of the sheet):
  timestamp | workshop | rating | comments | status
"""

import pandas as pd
import streamlit as st

# Replace this placeholder with your own published-to-web CSV URL.
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vREPLACE_ME/pub?output=csv"


@st.cache_data(ttl=60)
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    return df


st.set_page_config(page_title="Step 2: Feedback dashboard", page_icon="📊", layout="wide")
st.title("📊 Workshop feedback dashboard")
st.caption("Step 2 — live data from a public Google Sheet. Refreshes every 60 seconds.")

if "REPLACE_ME" in SHEET_CSV_URL:
    st.info(
        "**Setup needed.** Open `step2-read-public-sheet/app.py` and replace "
        "`SHEET_CSV_URL` with your own published-sheet CSV URL. See "
        "[`docs/02-publish-sheet-to-web.md`](../docs/02-publish-sheet-to-web.md) "
        "for the click-by-click walkthrough."
    )
    st.stop()

try:
    df = load_data(SHEET_CSV_URL)
except Exception as e:
    st.error(f"Couldn't load the sheet. Check `SHEET_CSV_URL` in the source.\n\n{e}")
    st.stop()

if df.empty:
    st.warning("The sheet is empty. Add a few rows below the header and refresh.")
    st.stop()

with st.sidebar:
    st.header("Filters")
    rating_min, rating_max = st.slider("Rating range", 1, 5, (1, 5))
    workshop_search = st.text_input("Workshop name contains", "")

filtered = df.copy()
if "rating" in filtered.columns:
    filtered = filtered[filtered["rating"].between(rating_min, rating_max, inclusive="both")]
if workshop_search and "workshop" in filtered.columns:
    filtered = filtered[filtered["workshop"].astype(str).str.contains(workshop_search, case=False, na=False)]

c1, c2, c3 = st.columns(3)
c1.metric("Total responses", len(filtered))
c2.metric("Mean rating", f"{filtered['rating'].mean():.2f}" if len(filtered) and "rating" in filtered.columns else "—")
c3.metric("Distinct workshops", filtered["workshop"].nunique() if "workshop" in filtered.columns else 0)

c4, c5 = st.columns(2)
with c4:
    st.subheader("Rating distribution")
    if "rating" in filtered.columns and len(filtered):
        st.bar_chart(filtered["rating"].value_counts().sort_index())
    else:
        st.info("No rating data to chart.")
with c5:
    st.subheader("Submissions per day")
    if "timestamp" in filtered.columns and filtered["timestamp"].notna().any():
        per_day = filtered.groupby(filtered["timestamp"].dt.date).size()
        st.line_chart(per_day)
    else:
        st.info("No timestamp data to chart.")

with st.expander("Show raw data"):
    st.dataframe(filtered, width="stretch", hide_index=True)
