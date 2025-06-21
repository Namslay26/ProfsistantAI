# pages/3_📈_Dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📈 Research Progress Dashboard")

# --- Check data ---

if "reading_list" not in st.session_state or not st.session_state.reading_list:
    st.warning("Your reading list is empty. Add papers on the Reading List page.")
    st.stop()

# --- Sync progress length with reading list ---
while len(st.session_state.progress) < len(st.session_state.reading_list):
    st.session_state.progress.append({"status": "To Read", "notes": ""})
while len(st.session_state.progress) > len(st.session_state.reading_list):
    st.session_state.progress.pop()

# --- Build DataFrame for analysis ---
data = []
for paper, progress in zip(st.session_state.reading_list, st.session_state.progress):
    data.append({
        "Title": paper["title"],
        "Status": progress.get("status", "To Read"),
        "Source": paper.get("source", "Unknown"),
        "Labels": ", ".join(paper.get("labels", []))
    })

df = pd.DataFrame(data)

# --- Pie Chart: Status Distribution ---
st.subheader("📘 Reading Progress")
status_counts = df["Status"].value_counts().reset_index()
status_counts.columns = ["Status", "Count"]
fig1 = px.pie(status_counts, values="Count", names="Status", title="Progress by Status")
st.plotly_chart(fig1, use_container_width=True)

# --- Bar Chart: Label Distribution ---
st.subheader("🏷️ Labels Overview")
# Split label strings into individual labels
all_labels = df["Labels"].str.split(", ").explode()
label_counts = all_labels.value_counts().reset_index()
label_counts.columns = ["Label", "Count"]
if not label_counts.empty:
    fig2 = px.bar(label_counts, x="Label", y="Count", title="Number of Papers per Label", text="Count")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No labels found. Add them in the Reading List.")

# --- Filters ---
st.markdown("---")
st.subheader("🧵 Filter Papers")

selected_status = st.selectbox("Filter by Status", ["All"] + df["Status"].unique().tolist())
selected_label = st.selectbox("Filter by Label", ["All"] + sorted(label_counts["Label"].unique().tolist() if not label_counts.empty else []))

filtered_df = df.copy()

if selected_status != "All":
    filtered_df = filtered_df[filtered_df["Status"] == selected_status]
if selected_label != "All":
    filtered_df = filtered_df[filtered_df["Labels"].str.contains(selected_label)]

st.markdown(f"### Showing {len(filtered_df)} papers")
st.dataframe(filtered_df[["Title", "Status", "Source", "Labels"]], use_container_width=True)
