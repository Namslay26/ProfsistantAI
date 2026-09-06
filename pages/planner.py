import json
import re
from datetime import date, datetime, timedelta

import streamlit as st
from google import genai

from auth import login, get_user_id
from database import get_user_papers
from ui import apply_theme, sidebar, page_header
from ai.provider import get_gemini_client, MODEL


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
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Page header
page_header(
    "PLANNER",
    "Turn research into a plan",
    "Choose the papers and goals you care about. Profsistant will turn them "
    "into manageable research sessions.",
)

# Check if papers exist
if not papers:
    st.info("Add papers to your Library before creating a research plan.")
    st.stop()

# Paper selection
paper_labels = [f"{i+1}. {p['title']}" for i, p in enumerate(papers)]
selected = st.pills(
    "Papers",
    paper_labels,
    selection_mode="multi",
    default=paper_labels[: min(5, len(paper_labels))],
)

# Research goal
goal = st.text_area(
    "Research goal",
    placeholder="What do you want to accomplish with these papers?",
)

# Date range
c1, c2 = st.columns(2)
with c1:
    start = st.date_input("Start date", value=date.today())
with c2:
    end = st.date_input("End date", value=date.today() + timedelta(days=6))

# Planning parameters
c1, c2, c3 = st.columns(3)
with c1:
    hours = st.slider("Hours per day", 0.5, 8.0, 1.5, 0.5)
with c2:
    study_time = st.time_input(
        "Preferred start time",
        value=datetime.strptime("18:00", "%H:%M").time(),
    )
with c3:
    style = st.segmented_control(
        "Planning style", ["Reading", "Research", "Balanced"], default="Balanced"
    )

days = st.pills(
    "Study days",
    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    selection_mode="multi",
    default=["Mon", "Tue", "Wed", "Thu", "Fri"],
)

# Validate date range
if end < start:
    st.error("End date must be on or after the start date.")
    st.stop()
# Generate plan
if st.button("✨ Generate plan", type="primary"):
    chosen = (
        [papers[paper_labels.index(x)] for x in selected]
        if selected
        else papers[:5]
    )
    context = "\n\n".join(
        [
            f"TITLE: {p['title']}\nABSTRACT: {(p.get('abstract') or '')[:3000]}"
            for p in chosen
        ]
    )
    prompt = (
        f"Create a realistic academic research plan. "
        f"Goal: {goal or 'Read and synthesize the selected papers.'}\n"
        f"Style: {style}\n"
        f"Date range: {start} to {end}\n"
        f"Available hours/day: {hours}\n"
        f"Study days: {days}\n"
        f"Papers:\n{context}\n\n"
        "Return ONLY a JSON array. Each object must have date (YYYY-MM-DD), task, "
        "paper_title, description, duration_minutes, priority (Low/Medium/High). "
        "Keep tasks small enough to complete in one session."
    )
    with st.status("Building your research plan…", expanded=True) as status:
        try:
            response=get_gemini_client().models.generate_content(model=MODEL,contents=prompt); text=re.sub(r"^```(?:json)?\s*|\s*```$","",response.text.strip()); st.session_state.generated_plan=json.loads(text); status.update(label="Plan ready",state="complete")
        except Exception as e:
            status.update(label="Plan generation failed", state="error")
            st.error(f"Could not create plan: {e}")
# Display generated plan
plan = st.session_state.get("generated_plan", [])
if plan:
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.subheader("Your plan")
    st.caption(
        "Edit the schedule below. Planner persistence will be connected to "
        "Supabase in the next pass."
    )

    # Editable plan table
    edited = st.data_editor(
        plan,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "date": st.column_config.TextColumn("Date"),
            "task": st.column_config.TextColumn("Task", width="large"),
            "paper_title": st.column_config.TextColumn("Paper", width="large"),
            "description": st.column_config.TextColumn("Details", width="large"),
            "duration_minutes": st.column_config.NumberColumn(
                "Minutes", min_value=10, max_value=480, step=5
            ),
            "priority": st.column_config.SelectboxColumn(
                "Priority", options=["Low", "Medium", "High"]
            ),
        },
    )
    st.session_state.generated_plan = edited.to_dict("records")

    # Daily view
    st.subheader("Daily view")
    grouped = {}
    for task in st.session_state.generated_plan:
        grouped.setdefault(task.get("date", "Unknown"), []).append(task)

    for d in sorted(grouped):
        with st.expander(d, expanded=True):
            for task in grouped[d]:
                title = task.get("task", "Untitled")
                paper = task.get("paper_title", "")
                mins = task.get("duration_minutes", 0)
                priority = task.get("priority", "Medium")
                desc = task.get("description", "")
                st.markdown(
                    f'<div class="task-card"><strong>{title}</strong><br>'
                    f'<span class="muted">{paper} · {mins} min · {priority} priority</span><br>'
                    f'<span class="muted">{desc}</span></div>',
                    unsafe_allow_html=True,
                )

    if st.button("Reset generated plan"):
        st.session_state.generated_plan = []
        st.rerun()
