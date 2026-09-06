import streamlit as st
from google import genai

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

st.title("💡 Gaps & Ideas Generator")

st.markdown(
    """
    Analyze the papers in your reading list and use Gemini
    to identify research gaps, follow-up questions, and
    potential project ideas.
    """
)


# ============================================================
# GEMINI
# ============================================================

api_key = st.secrets["GEMINI_API_KEY"]

client = genai.Client(
    api_key=api_key
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
# CHECK READING LIST
# ============================================================

if not papers:

    st.warning(
        "Your reading list is empty. "
        "Add papers from the Home page first."
    )

    st.stop()


st.success(
    f"Loaded {len(papers)} papers from your reading list."
)


# ============================================================
# PAPER SELECTION
# ============================================================

st.subheader("📚 Papers Being Analyzed")

for idx, paper in enumerate(papers):

    st.markdown(
        f"**{idx + 1}. {paper.get('title', 'Untitled')}**"
    )


# ============================================================
# PREPARE PAPERS FOR GEMINI
# ============================================================

paper_chunks = []

for paper in papers:

    title = paper.get(
        "title",
        "Untitled"
    )

    abstract = paper.get(
        "abstract",
        ""
    )

    if not abstract:
        abstract = "No abstract available."

    # Prevent an extremely large Gemini request.
    abstract = abstract[:3000]

    paper_chunks.append(
        f"""
Title: {title}

Abstract:
{abstract}
"""
    )


paper_context = "\n\n".join(
    paper_chunks
)


# ============================================================
# GENERATE IDEAS
# ============================================================

st.subheader(
    "🔍 Generate Research Gaps & Project Ideas"
)


if st.button(
    "✨ Generate with Gemini",
    type="primary"
):

    with st.spinner(
        "Analyzing your papers..."
    ):

        try:

            response = client.models.generate_content(

                model="gemini-3.5-flash",

                contents=f"""
You are an academic research assistant helping
a graduate student identify promising research
directions.

The student has the following papers in their
reading list:

{paper_context}

Analyze these papers collectively.

Identify:

1. Research gaps or limitations
   - What problems remain unsolved?
   - What limitations appear across multiple papers?

2. Interesting follow-up research questions
   - Questions that naturally emerge from the papers
   - Questions that could lead to publishable research

3. Small project ideas
   - Practical projects that could be implemented
   - Prefer ideas that could realistically be explored
     by a graduate student

4. Connections between the papers
   - Identify opportunities where ideas, methods,
     datasets, or approaches from different papers
     could be combined.

For each idea, explain briefly why it is interesting.

Be specific rather than giving generic research advice.

Organize the response using clear headings and
numbered or bulleted points.
"""
            )

            st.session_state.generated_ideas = (
                response.text
            )

            st.success(
                "✨ Research ideas generated!"
            )

        except Exception as e:

            st.error(
                "Unable to generate research ideas."
            )

            st.caption(
                f"Error: {e}"
            )


# ============================================================
# SHOW GENERATED IDEAS
# ============================================================

if "generated_ideas" in st.session_state:

    st.markdown("---")

    st.subheader(
        "🤖 Gemini Suggestions"
    )

    st.markdown(
        st.session_state.generated_ideas
    )


# ============================================================
# MANUAL IDEA ENTRY
# ============================================================

st.markdown("---")

st.subheader(
    "📝 Add Your Own Idea"
)


new_idea = st.text_area(
    "Enter your research idea",
    placeholder=(
        "e.g. Investigate whether differential "
        "privacy can be combined with federated "
        "learning for..."
    )
)


if st.button(
    "➕ Add Idea"
):

    if new_idea.strip():

        if "ideas_list" not in st.session_state:
            st.session_state.ideas_list = []

        st.session_state.ideas_list.append(
            new_idea.strip()
        )

        st.success(
            "Idea added!"
        )

    else:

        st.warning(
            "Please enter an idea first."
        )


# ============================================================
# SAVED IDEAS
# ============================================================

st.markdown("---")

st.subheader(
    "💡 Saved Ideas"
)


if (
    "ideas_list" not in st.session_state
    or not st.session_state.ideas_list
):

    st.info(
        "No saved ideas yet."
    )

else:

    for idx, idea in enumerate(
        st.session_state.ideas_list
    ):

        col1, col2 = st.columns(
            [5, 1]
        )

        with col1:

            st.markdown(
                f"**{idx + 1}.** {idea}"
            )

        with col2:

            if st.button(
                "❌",
                key=f"delete_idea_{idx}"
            ):

                st.session_state.ideas_list.pop(
                    idx
                )

                st.rerun()
