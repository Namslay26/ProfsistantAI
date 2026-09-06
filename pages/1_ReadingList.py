import streamlit as st

from auth import login, get_user_id
from database import (
    get_user_papers,
    update_paper,
    delete_paper,
    add_paper,
)


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Reading List",
    page_icon="📚",
    layout="wide",
)


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
# LOAD PAPERS
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
# PAGE HEADER
# ============================================================

st.title("📚 Your Research Reading List")

st.markdown(
    """
    Papers saved from your research searches are stored
    permanently in your Supabase reading list.
    """
)


# ============================================================
# EMPTY STATE
# ============================================================

if not papers:

    st.info(
        "Your reading list is empty. "
        "Search for papers on the Home page or add one below."
    )

else:

    st.success(
        f"You have {len(papers)} paper"
        f"{'s' if len(papers) != 1 else ''} "
        "in your reading list."
    )


# ============================================================
# CONSTANTS
# ============================================================

statuses = [
    "To Read",
    "Reading",
    "Done",
]

label_options = [
    "Survey",
    "Theoretical",
    "Empirical",
    "Review",
    "Application",
    "Methodology",
    "Dataset",
    "Benchmark",
]


# ============================================================
# DISPLAY PAPERS
# ============================================================

for idx, paper in enumerate(papers):

    paper_id = paper["id"]

    st.markdown("---")

    # ========================================================
    # TITLE
    # ========================================================

    st.subheader(
        f"{idx + 1}. {paper.get('title', 'Untitled')}"
    )

    # ========================================================
    # METADATA
    # ========================================================

    authors = paper.get(
        "authors",
        "Unknown"
    ) or "Unknown"

    st.markdown(
        f"**Authors:** {authors}"
    )

    metadata = []

    if paper.get("source"):
        metadata.append(
            f"📌 **Source:** {paper['source']}"
        )

    if paper.get("publication_year"):
        metadata.append(
            f"📅 **Year:** {paper['publication_year']}"
        )

    if paper.get("citation_count") is not None:
        metadata.append(
            f"📚 **Citations:** "
            f"{paper.get('citation_count', 0)}"
        )

    if metadata:
        st.markdown(
            "  \n".join(metadata)
        )

    # ========================================================
    # OPENALEX ID
    # ========================================================

    if paper.get("openalex_id"):

        with st.expander("🔎 Paper Metadata"):

            st.code(
                paper["openalex_id"],
                language=None
            )

    # ========================================================
    # LABELS
    # ========================================================

    labels = paper.get("labels") or []

    if isinstance(labels, str):

        labels = [
            label.strip()
            for label in labels.split(",")
            if label.strip()
        ]

    st.markdown(
        f"🏷️ **Labels:** "
        f"{', '.join(labels) if labels else 'None'}"
    )

    # ========================================================
    # PAPER LINKS
    # ========================================================

    url = paper.get("url")

    if url and url != "#":

        st.link_button(
            "🔗 View Paper",
            url
        )

    # ========================================================
    # ABSTRACT
    # ========================================================

    with st.expander("📄 Abstract"):

        abstract = paper.get(
            "abstract",
            ""
        ) or ""

        if abstract:

            st.write(
                abstract
            )

        else:

            st.caption(
                "No abstract available."
            )

    # ========================================================
    # STATUS
    # ========================================================

    current_status = paper.get(
        "status",
        "To Read"
    )

    if current_status not in statuses:
        current_status = "To Read"

    status_index = statuses.index(
        current_status
    )

    new_status = st.selectbox(
        "📘 Status",
        statuses,
        index=status_index,
        key=f"status_{paper_id}",
    )

    if new_status != paper.get("status", "To Read"):

        try:

            update_paper(
                paper_id,
                user_id,
                {
                    "status": new_status
                },
            )

            st.success(
                "Status updated!"
            )

            st.rerun()

        except Exception as e:

            st.error(
                "Unable to update status."
            )

            st.caption(
                f"Error: {e}"
            )

    # ========================================================
    # LABEL EDITING
    # ========================================================

    new_labels = st.multiselect(
        "🏷️ Labels",
        label_options,
        default=[
            label
            for label in labels
            if label in label_options
        ],
        key=f"labels_{paper_id}",
    )

    if set(new_labels) != set(labels):

        if st.button(
            "💾 Save Labels",
            key=f"save_labels_{paper_id}",
        ):

            try:

                update_paper(
                    paper_id,
                    user_id,
                    {
                        "labels": new_labels
                    },
                )

                st.success(
                    "Labels updated!"
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "Unable to update labels."
                )

                st.caption(
                    f"Error: {e}"
                )

    # ========================================================
    # NOTES
    # ========================================================

    current_notes = paper.get(
        "notes",
        ""
    ) or ""

    with st.form(
        f"notes_form_{paper_id}"
    ):

        new_notes = st.text_area(
            "📝 Notes",
            value=current_notes,
            key=f"notes_{paper_id}",
        )

        save_notes = st.form_submit_button(
            "💾 Save Notes"
        )

    if save_notes:

        try:

            update_paper(
                paper_id,
                user_id,
                {
                    "notes": new_notes
                },
            )

            st.success(
                "Notes saved!"
            )

            st.rerun()

        except Exception as e:

            st.error(
                "Unable to save notes."
            )

            st.caption(
                f"Error: {e}"
            )

    # ========================================================
    # DELETE
    # ========================================================

    if st.button(
        f"🗑️ Remove Paper #{idx + 1}",
        key=f"remove_{paper_id}",
    ):

        try:

            delete_paper(
                paper_id,
                user_id
            )

            st.success(
                "Paper removed."
            )

            st.rerun()

        except Exception as e:

            st.error(
                "Unable to remove paper."
            )

            st.caption(
                f"Error: {e}"
            )


# ============================================================
# ADD CUSTOM PAPER
# ============================================================

st.markdown("---")

st.subheader("➕ Add a Custom Paper")

st.caption(
    "Use this if you want to add a paper that was not found "
    "through OpenAlex."
)


with st.form("add_paper_form"):

    title = st.text_input(
        "Title"
    )

    authors = st.text_input(
        "Authors"
    )

    abstract = st.text_area(
        "Abstract"
    )

    url = st.text_input(
        "Optional URL"
    )

    source = st.selectbox(
        "📌 Source",
        [
            "Manual",
            "Google Scholar",
            "Conference",
            "ArXiv",
            "Advisor",
            "Other",
        ],
    )

    labels = st.multiselect(
        "🏷️ Labels",
        label_options,
    )

    submit = st.form_submit_button(
        "➕ Add to Reading List"
    )


# ============================================================
# ADD CUSTOM PAPER TO SUPABASE
# ============================================================

if submit:

    if not title.strip():

        st.warning(
            "Please enter the paper title."
        )

    elif not authors.strip():

        st.warning(
            "Please enter the authors."
        )

    elif not abstract.strip():

        st.warning(
            "Please enter the abstract."
        )

    else:

        try:

            add_paper(
                user_id=user_id,
                paper={
                    # No OpenAlex ID because this is
                    # a manually added paper.
                    "openalex_id": None,

                    "title": title.strip(),

                    "authors": authors.strip(),

                    "abstract": abstract.strip(),

                    "url": (
                        url.strip()
                        if url.strip()
                        else "#"
                    ),

                    "source": source,

                    "labels": labels,

                    "status": "To Read",

                    "notes": "",
                },
            )

            st.success(
                "✅ Paper added to your reading list!"
            )

            st.rerun()

        except Exception as e:

            st.error(
                "Unable to add the paper."
            )

            st.caption(
                f"Error: {e}"
            )
