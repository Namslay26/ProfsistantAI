# pages/4_💡_Gaps_and_Ideas.py

import streamlit as st
from google import genai
st.title("💡 Gaps & Ideas Generator")

# --- Setup Gemini ---
api_key = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=api_key)


# --- Load reading list ---
papers = st.session_state.get("reading_list", [])
if not papers:
    st.warning("Your reading list is empty. Add papers on the Home page.")
    st.stop()

# --- Generate prompt from paper titles and abstracts ---
paper_chunks = "\n\n".join(
    [f"Title: {p['title']}\nAbstract: {p['abstract']}" for p in papers]
)

# --- Show and trigger Gemini gap generation ---
st.subheader("🔍 Generate Research Gaps & Project Ideas")

if st.button("Generate with Gemini"):
    with st.spinner("Thinking deeply..."):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
            You are assisting a graduate student planning research.

            They are studying the following papers:

            {paper_chunks}

            Based on this reading list, identify:

            1. Research gaps or limitations across the papers
            2. Interesting follow-up research questions
            3. Small project ideas that could be pursued

            Respond clearly in bullets or a numbered list.
            """
        )
        st.session_state.generated_ideas = response.text
        st.success("✨ Ideas generated!")

# --- Show output ---
if "generated_ideas" in st.session_state:
    st.markdown("### 🤖 Gemini Suggestions")
    st.markdown(st.session_state.generated_ideas)

    if st.button("➕ Add to Ideas List"):
        if "ideas_list" not in st.session_state:
            st.session_state.ideas_list = []
        st.session_state.ideas_list.extend([
            idea.strip("• ").strip()
            for idea in st.session_state.generated_ideas.strip().split("\n")
            if idea.strip()
        ])
        st.success("Added to ideas list!")

# --- Manual idea entry ---
st.subheader("📝 Add Your Own Idea")
new_idea = st.text_area("Enter your idea")
if st.button("Add Idea"):
    if "ideas_list" not in st.session_state:
        st.session_state.ideas_list = []
    if new_idea.strip():
        st.session_state.ideas_list.append(new_idea.strip())
        st.success("Added!")

# --- Show and manage saved ideas ---
st.markdown("---")
st.subheader("💡 Saved Ideas")
if "ideas_list" not in st.session_state or not st.session_state.ideas_list:
    st.info("No saved ideas yet.")
else:
    for idx, idea in enumerate(st.session_state.ideas_list):
        st.markdown(f"**{idx+1}.** {idea}")
        if st.button(f"❌ Delete Idea #{idx+1}", key=f"del_idea_{idx}"):
            st.session_state.ideas_list.pop(idx)
            st.experimental_rerun()
