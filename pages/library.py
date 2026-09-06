import streamlit as st

from auth import login, get_user_id
from database import get_user_papers, update_paper, delete_paper, add_paper
from ui import apply_theme, sidebar, page_header, chips

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
    "LIBRARY",
    "Your research library",
    "Keep the papers that matter, annotate them, and move them through your research workflow.",
)

# Check if papers exist
if not papers:
    st.info("Your Library is empty. Search for a topic in Research and add your first paper.")
    st.stop()

# Filter papers by status and search
statuses = ["All", "To Read", "Reading", "Done"]
selected = st.pills("Status", statuses, default="All")
search = st.text_input(
    "Search library",
    placeholder="Search by title, author, or topic",
    label_visibility="collapsed",
)

filtered = []
for p in papers:
    if selected != "All" and p.get("status", "To Read") != selected:
        continue
    search_text = (
        f"{p.get('title', '')} {p.get('authors', '')} {p.get('abstract', '')}"
    ).lower()
    if search.strip() and search.strip().lower() not in search_text:
        continue
    filtered.append(p)

st.caption(f"{len(filtered)} paper{'s' if len(filtered) != 1 else ''}")
# Display papers
for p in filtered:
    pid = p["id"]
    labels = p.get("labels") or (
        [] if not isinstance(p.get("labels"), str) else [p.get("labels")]
    )

    # Paper card
    st.markdown('<div class="research-card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="research-card-title">{p.get("title", "Untitled")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="meta">{p.get("authors", "Unknown")} · '
        f'{p.get("publication_year") or "Year unknown"} · '
        f'{p.get("citation_count", 0)} citations</div>',
        unsafe_allow_html=True,
    )
    st.markdown(chips(labels), unsafe_allow_html=True)

    # Abstract preview
    abstract = p.get("abstract") or "No abstract available."
    preview = abstract[:350] + ("…" if len(abstract) > 350 else "")
    st.markdown(
        f'<p class="muted" style="line-height:1.55">{preview}</p>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Action buttons
    c1, c2, c3 = st.columns([1.2, 1.1, 1])
    with c1:
        options = statuses[1:]
        current = p.get("status", "To Read")
        status = st.selectbox(
            "Status",
            options,
            index=options.index(current) if current in options else 0,
            key=f"status_{pid}",
            label_visibility="collapsed",
        )
        if status != current:
            update_paper(pid, user_id, {"status": status})
            st.rerun()
    with c2:
        if p.get("url") and p.get("url") != "#":
            st.link_button("View paper ↗", p["url"])
    with c3:
        if st.button("Delete", key=f"delete_{pid}"):
            delete_paper(pid, user_id)
            st.toast("Paper removed from Library")
            st.rerun()

    # Notes expander
    with st.expander("Notes & details"):
        notes = st.text_area(
            "Notes", value=p.get("notes") or "", key=f"notes_{pid}"
        )
        if st.button("Save notes", key=f"save_notes_{pid}"):
            update_paper(pid, user_id, {"notes": notes})
            st.toast("Notes saved")
        st.markdown(
            f"**Source:** {p.get('source', 'Unknown')}  \n"
            f"**OpenAlex ID:** `{p.get('openalex_id') or 'Manual paper'}`"
        )
    st.divider()
# Add paper manually
with st.expander("＋ Add a paper manually"):
    with st.form("manual_paper"):
        title = st.text_input("Title")
        authors = st.text_input("Authors")
        year = st.number_input(
            "Publication year", min_value=1800, max_value=2100, value=2026
        )
        url = st.text_input("Paper URL")
        abstract = st.text_area("Abstract")
        source = st.selectbox(
            "Source", ["Manual", "ArXiv", "Conference", "Advisor", "Other"]
        )
        submitted = st.form_submit_button("Add to Library", type="primary")

    if submitted:
        if not title.strip():
            st.warning("Title is required.")
        else:
            add_paper(
                user_id,
                {
                    "openalex_id": None,
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "url": url or "#",
                    "source": source,
                    "labels": [],
                    "status": "To Read",
                    "notes": "",
                    "publication_year": int(year),
                    "citation_count": 0,
                },
            )
            st.toast("Paper added to Library")
            st.rerun()
