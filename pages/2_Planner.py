from google import genai
import streamlit as st 
from ics import Calendar, Event
from datetime import datetime, timedelta
import pytz
import io
import os

# --- Gemini setup ---

api_key = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=api_key)


st.title("🧠 Research Planner")

# --- Reading List Check ---
if "reading_list" not in st.session_state or not st.session_state.reading_list:
    st.warning("Your reading list is empty. Add papers on the home page.")
else:
    st.subheader("📅 Your Availability")

    # --- User Inputs ---
    total_weeks = st.slider("How many weeks do you want to plan for?", 1, 12, 4)

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    selected_days = st.multiselect("Select days you're available:", days_of_week, default=["Monday", "Wednesday", "Friday"])

    time_range = st.slider("What time are you free on those days?",
                           min_value=6, max_value=22, value=(17, 19),
                           format="%d:00")

    start_hour, end_hour = time_range
    task_types = ["Read", "Take Notes", "Brainstorm"]
    papers = st.session_state.reading_list
    total_tasks = len(papers) * len(task_types)

    # --- Gemini Plan Preview ---
    if st.button("🔮 Show Suggested Plan (Gemini)"):
        with st.spinner("Generating with Gemini..."):
            titles = [p["title"] for p in papers]
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"""
                Help a student plan reading and analysis for these papers:

                {titles}

                They are available on {', '.join(selected_days)} between {start_hour}:00 and {end_hour}:00, and they want to finish in {total_weeks} weeks.

                Suggest a weekly schedule with tasks like "Read Paper", "Take Notes", "Brainstorm Ideas". Present clearly by weeks and days.
                """
            )
            st.markdown("### 🧠 Gemini's Suggested Weekly Plan")
            st.markdown(response.text)

    # --- Calendar Export Logic ---
    if st.button("📅 Generate Downloadable Calendar (.ics)"):
        with st.spinner("Building your research calendar..."):
            calendar = Calendar()
            days_map = {
                "Monday": 0, "Tuesday": 1, "Wednesday": 2,
                "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
            }
            selected_day_nums = [days_map[d] for d in selected_days]

            start_date = datetime.today()
            current_date = start_date
            task_counter = 0

            for week in range(total_weeks):
                for day in selected_day_nums:
                    while current_date.weekday() != day:
                        current_date += timedelta(days=1)
                    
                    for hour in range(start_hour, end_hour):
                        if task_counter >= total_tasks:
                            break
                        paper_idx = task_counter // len(task_types)
                        task_type = task_types[task_counter % len(task_types)]

                        event = Event()
                        event.name = f"{task_type} Paper {paper_idx + 1}"
                        event.begin = datetime(current_date.year, current_date.month, current_date.day, hour, 0, tzinfo=pytz.utc)
                        event.end = datetime(current_date.year, current_date.month, current_date.day, hour + 1, 0, tzinfo=pytz.utc)
                        event.description = f"{task_type} session for '{papers[paper_idx]['title'][:40]}...'"
                        calendar.events.add(event)
                        task_counter += 1

                    current_date += timedelta(days=1)
                    if task_counter >= total_tasks:
                        break

            with io.BytesIO() as f:
                f.write(str(calendar).encode("utf-8"))
                f.seek(0)
                st.download_button(
                    label="📥 Download Research Calendar (.ics)",
                    data=f,
                    file_name="profsistant_schedule.ics",
                    mime="text/calendar"
                )