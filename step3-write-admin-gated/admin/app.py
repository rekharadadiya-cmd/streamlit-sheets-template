"""Step 3 (admin): Password-gated dashboard + editor over the same sheet.

A single shared password (from st.secrets["admin_password"]) gates access.
This is NOT real authentication — it's the simplest thing that works for a
small private dashboard. See docs/04-adapt-to-your-niche.md for upgrade paths.
"""

import gspread
import pandas as pd
import streamlit as st


@st.cache_resource
def get_worksheet():
    creds = dict(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds)
    return client.open_by_key(st.secrets["sheet_id"]).sheet1


def login_gate() -> bool:
    if st.session_state.get("authed"):
        return True
    st.title("🔒 Admin")
    pw = st.text_input("Password", type="password")
    if st.button("Sign in"):
        if pw and pw == st.secrets.get("admin_password"):
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("Wrong password.")
    return False


def load_df(ws) -> pd.DataFrame:
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    return df


st.set_page_config(page_title="Admin: feedback", page_icon="🔒", layout="wide")

if not login_gate():
    st.stop()

ws = get_worksheet()
df = load_df(ws)

if df.empty:
    st.info("No responses yet. Once people submit via the collect app, they'll show up here.")
    st.stop()

dashboard_tab, manage_tab = st.tabs(["📊 Dashboard", "✏️ Manage"])

with dashboard_tab:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total responses", len(df))
    c2.metric("Mean rating", f"{df['rating'].mean():.2f}" if "rating" in df.columns else "—")
    c3.metric(
        "New (unreviewed)",
        int((df["status"] == "new").sum()) if "status" in df.columns else 0,
    )

    c4, c5 = st.columns(2)
    with c4:
        st.subheader("Rating distribution")
        if "rating" in df.columns:
            st.bar_chart(df["rating"].value_counts().sort_index())
    with c5:
        st.subheader("Submissions per day")
        if "timestamp" in df.columns and df["timestamp"].notna().any():
            st.line_chart(df.groupby(df["timestamp"].dt.date).size())

with manage_tab:
    st.caption("Edit the `status` column inline, then click **Save changes**.")
    editable_columns = [c for c in df.columns if c != "status"]
    edited = st.data_editor(
        df,
        width="stretch",
        hide_index=True,
        disabled=editable_columns,
        column_config=(
            {"status": st.column_config.SelectboxColumn(options=["new", "reviewed", "archived"])}
            if "status" in df.columns
            else None
        ),
        num_rows="fixed",
        key="editor",
    )

    if st.button("Save changes"):
        if "status" not in df.columns:
            st.error("This sheet has no `status` column to save.")
        else:
            changed_mask = edited["status"].astype(str) != df["status"].astype(str)
            n_changed = int(changed_mask.sum())
            if n_changed == 0:
                st.info("Nothing to save.")
            else:
                status_col_idx = list(df.columns).index("status") + 1  # gspread is 1-indexed
                for pos in edited.index[changed_mask]:
                    sheet_row = int(pos) + 2  # +1 for header, +1 for 1-indexing
                    ws.update_cell(sheet_row, status_col_idx, str(edited.at[pos, "status"]))
                st.cache_resource.clear()
                st.success(f"Saved {n_changed} change(s). Refresh to see updated data.")
