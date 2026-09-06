import json
import re
from datetime import datetime, date, time, timedelta

import streamlit as st
from google import genai

from auth import login, get_user_id
from database import get_user_papers


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Research Planner",
    page_icon="🗓️",
    layout="wide",
)

GEMINI_MODEL = "gemini-3.5-flash"


# ============================================================
# AUTH
# ============================================================

if "user" not in st.session_state:
    login()
    st.stop()

user_id = get_user_id()

if not user_id:
    st.error("Unable to identify the logged-in user.")
    st.stop()


# ============================================================
# GEMINI
# ============================================================

gemini_client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# ============================================================
# SESSION STATE
# ============================================================

if "generated_plan" not in st.session_state:
    st.session_state.generated_plan = []

if "planner_topic" not in st.session_state:
    st.session_state.planner_topic = ""


# ============================================================
# HELPERS
# ============================================================

def clean_json_response(text):
    """
    Remove markdown code fences if Gemini returns JSON
    inside ```json ... ``` blocks.
    """

    if not text:
        return ""

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```\s*",
        "",
        text,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    return text.strip()


def build_calendar_event(
    task,
    start_datetime,
    duration_minutes,
):
    """
    Build one ICS VEVENT.
    """

    end_datetime = (
        start_datetime
        + timedelta(minutes=duration_minutes)
    )

    dt_start = start_datetime.strftime(
        "%Y%m%dT%H%M%S"
    )

    dt_end = end_datetime.strftime(
        "%Y%m%dT%H%M%S"
    )

    title = task.get(
        "task",
        "Research Study Session",
    )

    paper = task.get(
        "paper_title",
        "",
    )

    description = task.get(
        "description",
        "",
    )

    if paper:
        description = (
            f"Paper: {paper}\\n"
            f"{description}"
        )

    return (
        "BEGIN:VEVENT\n"
        f"DTSTART:{dt_start}\n"
        f"DTEND:{dt_end}\n"
        f"SUMMARY:{title}\n"
        f"DESCRIPTION:{description}\n"
        "END:VEVENT\n"
    )


def create_ics(plan, start_time):
    """
    Convert the generated plan into an .ics calendar file.
    """

    events = []

    for task in plan:

        try:

            task_date = datetime.strptime(
                task["date"],
                "%Y-%m-%d",
            ).date()

        except (KeyError, ValueError):

            continue

        duration = int(
            task.get(
                "duration_minutes",
                60,
            )
        )

        start_datetime = datetime.combine(
            task_date,
            start_time,
        )

        events.append(
            build_calendar_event(
                task,
                start_datetime,
                duration,
            )
        )

    calendar = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//Profsistant AI//Research Planner//EN\n"
        "CALSCALE:GREGORIAN\n"
        "METHOD:PUBLISH\n"
        + "".join(events)
        + "END:VCALENDAR\n"
    )

    return calendar


def generate_plan(
    papers,
    start_date,
    end_date,
    hours_per_day,
    study_days,
    planning_style,
    research_goal,
):
    """
    Ask Gemini to create a structured research plan.
    """

    paper_context = []

    for paper in papers:

        abstract = (
            paper.get("abstract", "")
            or "No abstract available."
        )

        # Keep the Gemini request manageable.
        abstract = abstract[:3000]

        paper_context.append(
            f"""
TITLE:
{paper.get("title", "Untitled")}

AUTHORS:
{paper.get("authors", "Unknown")}

YEAR:
{paper.get("publication_year", "Unknown")}

ABSTRACT:
{abstract}
"""
        )

    papers_text = "\n\n".join(
        paper_context
    )

    prompt = f"""
You are an academic research planning assistant.

Create a realistic research reading and study plan
for a graduate student.

RESEARCH GOAL:
{research_goal}

PLANNING PERIOD:
{start_date.isoformat()} to {end_date.isoformat()}

AVAILABLE STUDY TIME:
{hours_per_day} hours per study day

STUDY DAYS:
{", ".join(study_days)}

PLANNING STYLE:
{planning_style}

PAPERS:
{papers_text}

Create a schedule that helps the student:

1. Read and understand the selected papers.
2. Compare related approaches.
3. Identify methodologies and important concepts.
4. Take useful research notes.
5. Progress toward the stated research goal.
6. Reserve time for synthesis and identifying research gaps.

Do not simply assign one paper per day.

Break difficult papers into multiple sessions when useful.

For example, sessions could include:
- Abstract and introduction
- Related work
- Methodology
- Results
- Critical reading
- Notes
- Comparison with another paper
- Research gap analysis
- Synthesis

Return ONLY valid JSON.

The JSON must be an array with objects using exactly
these fields:

[
  {{
    "date": "YYYY-MM-DD",
    "task": "Short task title",
    "paper_title": "Paper title or empty string",
    "description": "What the student should accomplish",
    "duration_minutes": 60,
    "priority": "High"
  }}
]

Rules:

- Only schedule dates between the planning period.
- Only use the specified study days.
- Do not exceed {hours_per_day} hours on any study day.
- Keep individual sessions between 30 and 120 minutes.
- Use realistic workloads.
- Include review/synthesis sessions.
- Prioritize foundational papers before highly dependent papers.
- If several papers overlap strongly, schedule a comparison session.
- Do not invent paper titles.
"""

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    raw_text = clean_json_response(
        response.text
    )

    return json.loads(raw_text)


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🗓️ Research Planner")

st.markdown(
    """
    Turn your reading list into a realistic research plan.

    **Choose what you want to study → tell Profsistant
    how much time you have → let Gemini build the plan.**
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
# EMPTY STATE
# ============================================================

if not papers:

    st.info(
        "Your reading list is empty."
    )

    st.markdown(
        """
        Start by adding some papers from the **Home** page.
        Once you have papers in your reading list, Profsistant
        can build a personalized research plan for you.
        """
    )

    st.stop()


# ============================================================
# OVERVIEW
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "📚 Papers",
        len(papers),
    )

with col2:

    completed = sum(
        1
        for paper in papers
        if paper.get("status") == "Done"
    )

    st.metric(
        "✅ Completed",
        completed,
    )

with col3:

    to_read = sum(
        1
        for paper in papers
        if paper.get("status") == "To Read"
    )

    st.metric(
        "📖 To Read",
        to_read,
    )


# ============================================================
# STEP 1 — SELECT PAPERS
# ============================================================

st.markdown("---")

st.header("1️⃣ Choose your papers")

st.caption(
    "Select the papers you want Profsistant to include "
    "in this study plan."
)


paper_options = [
    paper["title"]
    for paper in papers
]


selected_titles = st.pills(
    "Papers to include",
    paper_options,
    selection_mode="multi",
    default=paper_options,
    width="stretch",
)


selected_papers = [
    paper
    for paper in papers
    if paper["title"] in (selected_titles or [])
]


if not selected_papers:

    st.warning(
        "Select at least one paper to create a plan."
    )


# ============================================================
# SELECTED PAPER PREVIEW
# ============================================================

if selected_papers:

    with st.expander(
        f"📚 {len(selected_papers)} papers selected",
        expanded=False,
    ):

        for paper in selected_papers:

            status = paper.get(
                "status",
                "To Read",
            )

            st.markdown(
                f"**{paper['title']}**  \n"
                f"Status: `{status}`"
            )


# ============================================================
# STEP 2 — RESEARCH GOAL
# ============================================================

st.header("2️⃣ What's your goal?")

research_goal = st.text_area(
    "Research goal",
    placeholder=(
        "Example: Understand how differential privacy "
        "can be applied to federated learning and identify "
        "a possible research gap for a project."
    ),
    height=100,
)


# ============================================================
# STEP 3 — PLANNING PREFERENCES
# ============================================================

st.header("3️⃣ Planning preferences")


# ------------------------------------------------------------
# Planning style
# ------------------------------------------------------------

planning_style = st.segmented_control(
    "How should Profsistant structure your plan?",
    [
        "📖 Reading-focused",
        "🔬 Research-focused",
        "⚖️ Balanced",
    ],
    default="⚖️ Balanced",
    width="stretch",
)


# ------------------------------------------------------------
# Dates
# ------------------------------------------------------------

date_col1, date_col2 = st.columns(2)

with date_col1:

    start_date = st.date_input(
        "📅 Start date",
        value=date.today(),
        min_value=date.today(),
    )

with date_col2:

    default_end_date = (
        start_date
        + timedelta(days=14)
    )

    end_date = st.date_input(
        "📅 End date",
        value=default_end_date,
        min_value=start_date,
    )


# ------------------------------------------------------------
# Study time
# ------------------------------------------------------------

time_col1, time_col2 = st.columns(2)

with time_col1:

    hours_per_day = st.slider(
        "⏱️ Study hours per day",
        min_value=0.5,
        max_value=8.0,
        value=2.0,
        step=0.5,
    )

with time_col2:

    start_time = st.time_input(
        "🕐 Preferred study time",
        value=time(19, 0),
    )


# ------------------------------------------------------------
# Study days
# ------------------------------------------------------------

study_days = st.pills(
    "📆 Which days can you study?",
    [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ],
    selection_mode="multi",
    default=[
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
    ],
    width="stretch",
)


# ============================================================
# PLAN SUMMARY
# ============================================================

st.markdown("---")

st.subheader("📋 Plan summary")

summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:

    st.metric(
        "Planning period",
        f"{(end_date - start_date).days + 1} days",
    )

with summary_col2:

    st.metric(
        "Daily study time",
        f"{hours_per_day:g} hrs",
    )

with summary_col3:

    st.metric(
        "Papers",
        len(selected_papers),
    )


# ============================================================
# GENERATE PLAN
# ============================================================

st.markdown("---")

generate_button = st.button(
    "✨ Generate Research Plan",
    type="primary",
    width="stretch",
)


if generate_button:

    if not selected_papers:

        st.warning(
            "Please select at least one paper."
        )

    elif not research_goal.strip():

        st.warning(
            "Tell Profsistant what you're trying to achieve "
            "with this reading plan."
        )

    elif not study_days:

        st.warning(
            "Select at least one study day."
        )

    elif start_date > end_date:

        st.warning(
            "The start date must be before the end date."
        )

    else:

        with st.status(
            "🧠 Building your research plan...",
            expanded=True,
        ) as status:

            try:

                st.write(
                    "Analyzing your selected papers..."
                )

                plan = generate_plan(
                    papers=selected_papers,
                    start_date=start_date,
                    end_date=end_date,
                    hours_per_day=hours_per_day,
                    study_days=study_days,
                    planning_style=planning_style,
                    research_goal=research_goal,
                )

                st.write(
                    f"Generated {len(plan)} study sessions."
                )

                st.session_state.generated_plan = plan

                st.session_state.planner_topic = (
                    research_goal.strip()
                )

                status.update(
                    label="✅ Research plan ready!",
                    state="complete",
                    expanded=False,
                )

                st.toast(
                    "Research plan generated!",
                    icon="🎉",
                )

            except json.JSONDecodeError:

                status.update(
                    label="❌ Gemini returned an invalid plan.",
                    state="error",
                    expanded=True,
                )

                st.error(
                    "Gemini did not return valid JSON. "
                    "Try generating the plan again."
                )

            except Exception as e:

                status.update(
                    label="❌ Could not generate the plan.",
                    state="error",
                    expanded=True,
                )

                st.error(
                    "Something went wrong while generating "
                    "your research plan."
                )

                st.caption(
                    f"Error: {e}"
                )


# ============================================================
# DISPLAY GENERATED PLAN
# ============================================================

plan = st.session_state.generated_plan


if plan:

    st.markdown("---")

    st.header("4️⃣ Your Research Plan")

    st.caption(
        "You can edit the schedule below before exporting it."
    )


    # ========================================================
    # PLAN DATA
    # ========================================================

    plan_rows = []

    for index, task in enumerate(plan):

        plan_rows.append(
            {
                "Date": task.get(
                    "date",
                    "",
                ),

                "Task": task.get(
                    "task",
                    "",
                ),

                "Paper": task.get(
                    "paper_title",
                    "",
                ),

                "Description": task.get(
                    "description",
                    "",
                ),

                "Minutes": int(
                    task.get(
                        "duration_minutes",
                        60,
                    )
                ),

                "Priority": task.get(
                    "priority",
                    "Medium",
                ),
            }
        )


    # ========================================================
    # EDITABLE PLAN
    # ========================================================

    edited_plan = st.data_editor(
        plan_rows,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        key="research_plan_editor",
        column_config={
            "Date": st.column_config.TextColumn(
                "📅 Date",
                help="Use YYYY-MM-DD",
            ),

            "Task": st.column_config.TextColumn(
                "📝 Task",
            ),

            "Paper": st.column_config.TextColumn(
                "📚 Paper",
            ),

            "Description": st.column_config.TextColumn(
                "🎯 What to accomplish",
                width="large",
            ),

            "Minutes": st.column_config.NumberColumn(
                "⏱️ Minutes",
                min_value=30,
                max_value=240,
                step=15,
            ),

            "Priority": st.column_config.SelectboxColumn(
                "Priority",
                options=[
                    "High",
                    "Medium",
                    "Low",
                ],
            ),
        },
    )


    # ========================================================
    # SAVE EDITED PLAN
    # ========================================================

    if st.button(
        "💾 Save Changes to Plan"
    ):

        updated_plan = []

        for row in edited_plan:

            updated_plan.append(
                {
                    "date": row["Date"],
                    "task": row["Task"],
                    "paper_title": row["Paper"],
                    "description": row["Description"],
                    "duration_minutes": int(
                        row["Minutes"]
                    ),
                    "priority": row["Priority"],
                }
            )

        st.session_state.generated_plan = (
            updated_plan
        )

        st.toast(
            "Plan updated!",
            icon="💾",
        )

        st.rerun()


    # ========================================================
    # DAILY BREAKDOWN
    # ========================================================

    st.markdown("---")

    st.subheader("🗓️ Daily Breakdown")


    grouped = {}

    for task in st.session_state.generated_plan:

        task_date = task.get(
            "date",
            "",
        )

        if task_date not in grouped:
            grouped[task_date] = []

        grouped[task_date].append(
            task
        )


    for task_date in sorted(grouped.keys()):

        day_tasks = grouped[task_date]

        total_minutes = sum(
            int(
                task.get(
                    "duration_minutes",
                    60,
                )
            )
            for task in day_tasks
        )

        try:

            display_date = datetime.strptime(
                task_date,
                "%Y-%m-%d",
            ).strftime(
                "%A, %d %B %Y"
            )

        except ValueError:

            display_date = task_date


        with st.expander(
            f"📅 {display_date} "
            f"• {total_minutes // 60}h "
            f"{total_minutes % 60}m",
            expanded=True,
        ):

            for task in day_tasks:

                priority = task.get(
                    "priority",
                    "Medium",
                )

                priority_icon = {
                    "High": "🔴",
                    "Medium": "🟡",
                    "Low": "🟢",
                }.get(
                    priority,
                    "⚪",
                )

                st.markdown(
                    f"### {priority_icon} "
                    f"{task.get('task', 'Study Session')}"
                )

                if task.get("paper_title"):

                    st.markdown(
                        f"📚 **Paper:** "
                        f"{task['paper_title']}"
                    )

                st.markdown(
                    f"⏱️ **Duration:** "
                    f"{task.get('duration_minutes', 60)} minutes"
                )

                if task.get("description"):

                    st.write(
                        task["description"]
                    )

                st.markdown("---")


    # ========================================================
    # CALENDAR EXPORT
    # ========================================================

    st.markdown("---")

    st.header("5️⃣ Add it to your calendar")

    st.write(
        "Export the plan as an `.ics` file and import it "
        "into Google Calendar, Apple Calendar, Outlook, "
        "or another calendar application."
    )


    calendar_data = create_ics(
        st.session_state.generated_plan,
        start_time,
    )


    download_col1, download_col2 = st.columns(
        2
    )

    with download_col1:

        st.download_button(
            label="📥 Download Calendar (.ics)",
            data=calendar_data,
            file_name="profsistant_research_plan.ics",
            mime="text/calendar",
            width="stretch",
        )

    with download_col2:

        st.info(
            "💡 Your calendar sessions will use your "
            "preferred study time."
        )


    # ========================================================
    # RESEARCH PLAN RESET
    # ========================================================

    st.markdown("---")

    if st.button(
        "🔄 Create a New Plan"
    ):

        st.session_state.generated_plan = []

        st.rerun()
