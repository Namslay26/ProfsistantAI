import pandas as pd

import streamlit as st

from auth import login, get_user_id
from database import get_user_papers
from ui import apply_theme, sidebar, page_header, stat_card

# Initialize theme and sidebar
apply_theme()
sidebar()

# Check user authentication
if "user" not in st.session_state:
    login()
    st.stop()

# Get user data
user_id = get_user_id()
papers = get_user_papers(user_id)

# Page header
page_header(
    "PROGRESS",
    "Your research progress",
    "A lightweight view of what you have collected, read, and explored so far.",
)

# Calculate statistics
total = len(papers)
done = sum(1 for p in papers if p.get("status") == "Done")
reading = sum(1 for p in papers if p.get("status") == "Reading")
citations = sum(int(p.get("citation_count") or 0) for p in papers)

# Display stat cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    stat_card(total, "Papers in Library")
with c2:
    stat_card(reading, "Currently Reading")
with c3:
    stat_card(done, "Papers Completed")
with c4:
    stat_card(citations, "Citations Collected")

# Check if papers exist
if not papers:
    st.info("Your progress will appear here once you start building your Library.")
    st.stop()

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)

# Prepare data for visualization
rows = []
for p in papers:
    labels = p.get("labels") or []
    if isinstance(labels, str):
        labels = [labels]
    rows.append(
        {
            "Title": p.get("title", "Untitled"),
            "Status": p.get("status", "To Read"),
            "Year": p.get("publication_year"),
            "Citations": p.get("citation_count", 0),
            "Labels": ", ".join(labels),
        }
    )

df = pd.DataFrame(rows)

# Display charts
c1, c2 = st.columns(2)
with c1:
    st.subheader("Reading status")
    st.bar_chart(df["Status"].value_counts())

with c2:
    st.subheader("Papers by year")
    year_df = df.dropna(subset=["Year"])
    if not year_df.empty:
        st.bar_chart(year_df.groupby("Year").size())
    else:
        st.caption("Publication years are not available yet.")

# Library overview table
st.subheader("Library overview")
st.dataframe(df, use_container_width=True, hide_index=True)
