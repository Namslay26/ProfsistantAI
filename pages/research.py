import requests

import streamlit as st
from google import genai

from auth import login, get_user_id
from database import get_supabase, add_paper
from ui import apply_theme, sidebar, page_header, chips
from ai.provider import get_gemini_client, MODEL

# Initialize theme and sidebar
apply_theme()
sidebar()

# Check user authentication
if "user" not in st.session_state:
    login()
    st.stop()

# Initialize clients and constants
user_id = get_user_id()
supabase = get_supabase()
OPENALEX_URL = "https://api.openalex.org/works"


# Helper functions
def reconstruct_abstract(index):
    """Reconstruct abstract from inverted index."""
    if not index:
        return ""
    words = []
    for word, positions in index.items():
        for pos in positions:
            words.append((pos, word))
    words.sort(key=lambda x: x[0])
    return " ".join(w for _, w in words)


def search_openalex(topic):
    """Search OpenAlex for papers matching a topic."""
    params = {
        "search": topic,
        "per-page": 10,
        "select": (
            "id,doi,title,publication_year,cited_by_count,authorships,"
            "primary_location,open_access,abstract_inverted_index"
        ),
    }
    if "OPENALEX_EMAIL" in st.secrets:
        params["mailto"] = st.secrets["OPENALEX_EMAIL"]

    r = requests.get(OPENALEX_URL, params=params, timeout=15)
    r.raise_for_status()

    out = []
    for work in r.json().get("results", []):
        authors = [
            a["author"]["display_name"]
            for a in work.get("authorships", [])
            if a.get("author")
        ]
        loc = work.get("primary_location") or {}
        out.append(
            {
                "openalex_id": work.get("id"),
                "title": work.get("title") or "Untitled paper",
                "authors": ", ".join(authors) or "Unknown authors",
                "abstract": (
                    reconstruct_abstract(work.get("abstract_inverted_index"))
                    or "No abstract available."
                ),
                "publication_year": work.get("publication_year"),
                "citation_count": work.get("cited_by_count", 0),
                "url": (
                    loc.get("landing_page_url") or work.get("doi") or "#"
                ),
                "pdf_url": loc.get("pdf_url"),
                "is_open_access": (
                    work.get("open_access") or {}
                ).get("is_oa", False),
            }
        )
    return out[:5]


def existing_ids():
    """Get set of existing paper IDs for the current user."""
    r = supabase.table("papers").select("openalex_id").eq("user_id", user_id).execute()
    return {p.get("openalex_id") for p in (r.data or []) if p.get("openalex_id")}


# Page header
page_header(
    "RESEARCH",
    "What are you researching today?",
    "Search academic literature, save useful papers to your library, and build "
    "the foundation for your next research project.",
)

st.markdown("<div style='height:.9rem'></div>", unsafe_allow_html=True)

# Search form
with st.form("research_search", clear_on_submit=False):
    topic = st.text_input(
        "Research topic or question",
        placeholder="e.g. privacy-preserving federated learning",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("🔎 Search research", type="primary")

if submitted:
    if not topic.strip():
        st.warning("Enter a research topic or question first.")
        st.stop()

    with st.spinner("Searching the literature..."):
        try:
            papers = search_openalex(topic.strip())
        except requests.exceptions.Timeout:
            st.error("The literature search timed out. Please try again.")
            st.stop()
        except requests.exceptions.RequestException:
            st.error("Could not connect to the literature service. Please try again.")
            st.stop()
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.stop()

    st.session_state.search_results = papers
    st.session_state.last_search_topic = topic.strip()


# Display search results
if st.session_state.get("search_results"):
    papers = st.session_state.search_results
    query = st.session_state.get("last_search_topic", "your topic")
    saved = existing_ids()

    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.subheader(f'Papers for "{query}"')
    st.caption(f"Showing the {len(papers)} most relevant results.")

    for idx, paper in enumerate(papers, 1):
        with st.container(border=True):
            st.markdown(
                f'<div class="research-card-title">{idx}. {paper["title"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="meta">{paper["authors"]} · '
                f'{paper["publication_year"] or "Year unknown"} · '
                f'{paper["citation_count"]} citations</div>',
                unsafe_allow_html=True,
            )

            badges = ["Open access"] if paper["is_open_access"] else []
            badges.append("OpenAlex")
            st.markdown(chips(badges), unsafe_allow_html=True)

            abstract = paper["abstract"]
            preview = abstract[:420] + ("…" if len(abstract) > 420 else "")
            st.markdown(
                f'<p class="muted" style="margin-top:.75rem;line-height:1.6">{preview}</p>',
                unsafe_allow_html=True,
            )
            c1, c2, c3 = st.columns([1.25, 1, 1])
            with c1:
                if paper["openalex_id"] in saved:
                    st.success("✓ In Library")
                elif st.button("＋ Add to Library", key=f"add_{idx}"):
                    try:
                        add_paper(
                            user_id,
                            {
                                "openalex_id": paper["openalex_id"],
                                "title": paper["title"],
                                "authors": paper["authors"],
                                "abstract": paper["abstract"],
                                "url": paper["url"],
                                "source": "OpenAlex",
                                "labels": [],
                                "status": "To Read",
                                "notes": "",
                                "publication_year": paper["publication_year"],
                                "citation_count": paper["citation_count"],
                            },
                        )
                        st.toast("Paper added to your Library")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not add paper: {e}")

            with c2:
                if paper["url"] != "#":
                    st.link_button("View paper ↗", paper["url"])

            with c3:
                if paper["pdf_url"]:
                    st.link_button("Open PDF ↗", paper["pdf_url"])

            with st.expander("Read abstract / get AI insight"):
                st.markdown(paper["abstract"])
                if st.button("✨ Summarize this paper", key=f"summary_{idx}"):
                    with st.status("Analyzing paper…", expanded=False) as status:
                        try:
                            prompt = (
                                "You are helping a student understand an academic paper.\n"
                                f"Title: {paper['title']}\n"
                                f"Authors: {paper['authors']}\n"
                                f"Abstract: {paper['abstract'][:3000]}\n\n"
                                "Give: 3 bullet summary, problem, approach, contribution, "
                                "and one possible research direction. Keep it concise."
                            )
                            response = get_gemini_client().models.generate_content(
                                model=MODEL, contents=prompt
                            )
                            status.update(
                                label="Analysis complete", state="complete"
                            )
                            st.markdown(response.text)
                        except Exception as e:
                            status.update(label="Analysis failed", state="error")
                            st.error(str(e))
