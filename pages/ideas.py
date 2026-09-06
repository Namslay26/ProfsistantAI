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

# Initialize variables
user_id = get_user_id()
papers = get_user_papers(user_id)
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Page header
page_header(
    "IDEAS",
    "Explore where your research could go next",
    "Use your saved literature as a starting point for research gaps, questions, and small experiments.",
)

# Check if papers exist
if not papers:
    st.info("Add a few papers to your Library first.")
    st.stop()

# Create paper labels and selection
labels = [f"{i+1}. {p['title']}" for i, p in enumerate(papers)]
selected = st.pills(
    "Papers to analyze",
    labels,
    selection_mode="multi",
    default=labels[: min(5, len(labels))],
)

# Get research goal
goal = st.text_area(
    "Research goal (optional)",
    placeholder="e.g. Identify a feasible project in privacy-preserving federated learning.",
)

# Generate research directions
if st.button("✨ Generate research directions", type="primary"):
    chosen = chosen=[papers[labels.index(x)] for x in selected] if selected else papers[:5]
    context = "\n\n".join(
        [
            f"TITLE: {p['title']}\nABSTRACT: {(p.get('abstract') or '')[:3000]}"
            for p in chosen
        ]
    )
    prompt = (
        "You are a research assistant. Analyze these papers and suggest useful directions.\n"
        f"Research goal: {goal or 'Explore promising research directions.'}\n\n"
        f"{context}\n\n"
        "Return concise Markdown with four sections: Research gaps, Research questions, "
        "Small project ideas, Connections between papers. Do not invent claims not "
        "supported by the abstracts."
    )
    with st.status("Reading your selected papers…", expanded=True) as status:
        try:
            response=get_gemini_client().models.generate_content(model=MODEL,contents=prompt); st.session_state.generated_ideas=response.text; status.update(label="Research directions generated",state="complete")
        except Exception as e:
            status.update(label="Generation failed", state="error")
            st.error(str(e))

# Display generated ideas
if st.session_state.get("generated_ideas"):
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.markdown(st.session_state.generated_ideas)
    st.download_button(
        "Download ideas as Markdown",
        st.session_state.generated_ideas,
        file_name="profsistant_research_ideas.md",
    )
