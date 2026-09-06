import streamlit as st
import pandas as pd
import plotly.express as px

from auth import login, get_user_id
from database import get_user_papers


# ============================================================
# AUTHENTICATION
# ============================================================

if "user" not in st.session_state:
    login()
    st.stop()

user_id = get_user_id()

if not user_id:
    st.error("Unable to identify the logged-in user.")
    st.stop()


# ============================================================
# PAGE
# ============================================================

st.title("📈 Research Progress Dashboard")

st.markdown(
    """
    Track your reading progress, explore your research
    collection, and see how your reading list is evolving.
    """
)


# ============================================================
# LOAD PAPERS FROM SUPABASE
# ============================================================

try:

    papers = get_user_papers(user_id)

except Exception as e:

    st.error(
        "Unable to load your reading list."
    )

    st.caption(
        f"Error: {e}"
    )

    st.stop()


# ============================================================
# CHECK DATA
# ============================================================

if not papers:

    st.info(
        "Your reading list is empty. "
        "Add papers from the Home page."
    )

    st.stop()


st.success(
    f"You currently have {len(papers)} papers "
    f"in your reading list."
)


# ============================================================
# BUILD DATAFRAME
# ============================================================

data = []

for paper in papers:

    labels = paper.get("labels") or []

    # Supabase may return labels as a list.
    # This also handles a string gracefully.
    if isinstance(labels, str):
        labels = [
            label.strip()
            for label in labels.split(",")
            if label.strip()
        ]

    data.append({
        "ID": paper.get("id"),
        "Title": paper.get("title", "Untitled"),
        "Status": paper.get("status", "To Read"),
        "Source": paper.get("source", "Unknown"),
        "Labels": labels,
        "Year": paper.get("publication_year"),
        "Citations": paper.get("citation_count", 0),
    })


df = pd.DataFrame(data)


# ============================================================
# READING PROGRESS
# ============================================================

st.subheader("📘 Reading Progress")

status_counts = (
    df["Status"]
    .value_counts()
    .reset_index()
)

status_counts.columns = [
    "Status",
    "Count"
]


fig1 = px.pie(
    status_counts,
    values="Count",
    names="Status",
    title="Progress by Status"
)

st.plotly_chart(
    fig1,
    use_container_width=True
)


# ============================================================
# LABEL DISTRIBUTION
# ============================================================

st.subheader("🏷️ Labels Overview")

all_labels = []

for labels in df["Labels"]:
    all_labels.extend(labels)


if all_labels:

    label_counts = (
        pd.Series(all_labels)
        .value_counts()
        .reset_index()
    )

    label_counts.columns = [
        "Label",
        "Count"
    ]

    fig2 = px.bar(
        label_counts,
        x="Label",
        y="Count",
        title="Number of Papers per Label",
        text="Count"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

else:

    st.info(
        "No labels found. "
        "Add labels to your papers from the Reading List."
    )

    label_counts = pd.DataFrame(
        columns=["Label", "Count"]
    )


# ============================================================
# QUICK STATISTICS
# ============================================================

st.subheader("📊 Quick Statistics")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Total Papers",
        len(df)
    )

with col2:

    completed_count = (
        df["Status"] == "Completed"
    ).sum()

    st.metric(
        "Completed",
        completed_count
    )

with col3:

    total_citations = int(
        df["Citations"]
        .fillna(0)
        .sum()
    )

    st.metric(
        "Total Citations",
        total_citations
    )


# ============================================================
# FILTERS
# ============================================================

st.markdown("---")

st.subheader("🧵 Filter Papers")


status_options = [
    "All"
] + sorted(
    df["Status"]
    .dropna()
    .unique()
    .tolist()
)


label_options = [
    "All"
] + sorted(
    label_counts["Label"].tolist()
)


selected_status = st.selectbox(
    "Filter by Status",
    status_options
)


selected_label = st.selectbox(
    "Filter by Label",
    label_options
)


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df.copy()


if selected_status != "All":

    filtered_df = filtered_df[
        filtered_df["Status"] == selected_status
    ]


if selected_label != "All":

    filtered_df = filtered_df[
        filtered_df["Labels"].apply(
            lambda labels:
                selected_label in labels
        )
    ]


# ============================================================
# DISPLAY FILTERED PAPERS
# ============================================================

st.markdown(
    f"### Showing {len(filtered_df)} papers"
)


display_df = filtered_df.copy()

display_df["Labels"] = display_df[
    "Labels"
].apply(
    lambda labels: ", ".join(labels)
)


st.dataframe(
    display_df[
        [
            "Title",
            "Status",
            "Source",
            "Labels",
            "Year",
            "Citations"
        ]
    ],
    use_container_width=True,
    hide_index=True
)
