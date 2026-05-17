"""Step 1: Streamlit basics with mock data.

A small feedback form that stores submissions in session state. No external
services involved. Refresh the page and the data resets — that's the lesson:
in-memory data doesn't persist. Step 2 will fix that by reading from a real
Google Sheet.
"""

import datetime as dt

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Step 1: Mock feedback", page_icon="📝")
st.title("📝 Workshop feedback (mock changed)")
st.caption("Step 1 — data lives only in this browser tab. Refresh and it's gone.")

if "responses" not in st.session_state:
    st.session_state.responses = [
        {"timestamp": dt.datetime(2026, 5, 10, 14, 30), "workshop": "Intro to Python", "rating": 5, "comments": "Loved the pace."},
        {"timestamp": dt.datetime(2026, 5, 10, 14, 32), "workshop": "Intro to Python", "rating": 4, "comments": "More examples please."},
        {"timestamp": dt.datetime(2026, 5, 11, 10, 15), "workshop": "Pandas basics",    "rating": 5, "comments": ""},
    ]

with st.form("feedback_form", clear_on_submit=True):
    workshop = st.text_input("Workshop name", placeholder="e.g. Intro to Python")
    rating = st.slider("Rating", 1, 5, 4)
    comments = st.text_area("Comments", placeholder="Optional")
    submitted = st.form_submit_button("Submit")
    if submitted:
        if not workshop:
            st.error("Workshop name is required.")
        else:
            st.session_state.responses.append({
                "timestamp": dt.datetime.now(),
                "workshop": workshop,
                "rating": rating,
                "comments": comments,
            })
            st.success("Thanks! Your response was added to the table below.")

df = pd.DataFrame(st.session_state.responses)

st.subheader("Responses so far")
st.dataframe(df, use_container_width=True, hide_index=True)

st.subheader("Rating distribution")
st.bar_chart(df["rating"].value_counts().sort_index())
