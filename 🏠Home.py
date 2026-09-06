import re
import requests
import streamlit as st
from google import genai

from auth import login, get_user_id
from database import get_supabase, add_paper


OPENALEX_URL = "https://api.openalex.org/works"

# Retrieve 10 candidates from OpenAlex in one API call,
# then display the top 5.
SEARCH_CANDIDATES = 10
SEARCH_RESULTS_TO_SHOW = 5

# UI / Gemini limits
ABSTRACT_DISPLAY_LENGTH = 600
ABSTRACT_GEMINI_LENGTH = 3000

st.set_page_config(
    page_title="Profsistant AI",
    page_icon="📚",
    layout="wide"
)



if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "last_search_topic" not in st.session_state:
    st.session_state.last_search_topic = ""



if "user" not in st.session_state:
    login()
    st.stop()

user_id = get_user_id()

if not user_id:
    st.error("Unable to identify the logged-in user.")
    st.stop()



supabase = get_supabase()

gemini_client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


def reconstruct_abstract(inverted_index):
    """
    OpenAlex stores abstracts as an inverted index.

    Converts:
        {
            "this": [0],
            "is": [1],
            "an": [2],
            ...
        }

    back into a normal string.
    """

    if not inverted_index:
        return ""

    words = []

    for word, positions in inverted_index.items():
        for position in positions:
            words.append((position, word))

    words.sort(key=lambda x: x[0])

    return " ".join(word for _, word in words)


def normalize_text(text):
    """
    Normalize text for lightweight local comparison.
    """

    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def calculate_relevance(paper, query):
    """
    Lightweight local relevance score.

    OpenAlex already performs the primary topic-based
    relevance ranking. This function is only used as
    a secondary refinement.

    Higher scores mean the query has stronger overlap
    with the title and abstract.
    """

    query_normalized = normalize_text(query)
    title_normalized = normalize_text(paper.get("title", ""))
    abstract_normalized = normalize_text(paper.get("abstract", ""))

    if not query_normalized:
        return 0

    query_tokens = set(query_normalized.split())

    title_tokens = set(title_normalized.split())
    abstract_tokens = set(abstract_normalized.split())

    score = 0

    # Exact phrase in title
    if query_normalized in title_normalized:
        score += 100

    # Query token coverage in title
    if query_tokens:
        title_matches = len(query_tokens & title_tokens)
        score += title_matches * 15

    # Query token coverage in abstract
    if query_tokens:
        abstract_matches = len(query_tokens & abstract_tokens)
        score += abstract_matches * 3

    return score

def search_openalex(topic):
    """
    Search OpenAlex using the user's research topic.

    OpenAlex's `search` parameter searches across
    title, abstract, and full text.

    Only ONE API request is made per search.
    """

    params = {
        "search": topic,
        "per-page": SEARCH_CANDIDATES,
        "select": (
            "id,"
            "doi,"
            "title,"
            "publication_year,"
            "cited_by_count,"
            "authorships,"
            "primary_location,"
            "open_access,"
            "abstract_inverted_index"
        ),
    }

    if "OPENALEX_EMAIL" in st.secrets:
        params["mailto"] = st.secrets["OPENALEX_EMAIL"]

    response = requests.get(
        OPENALEX_URL,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    results = response.json().get("results", [])

    papers = []

    for work in results:


        authors = ", ".join(
            author.get("author", {}).get("display_name", "")
            for author in work.get("authorships", [])
            if author.get("author")
        )


        abstract = reconstruct_abstract(
            work.get("abstract_inverted_index")
        )


        primary_location = work.get("primary_location") or {}

        landing_page = primary_location.get(
            "landing_page_url"
        )

        pdf_url = primary_location.get("pdf_url")


        doi = work.get("doi")


        paper = {
            "openalex_id": work.get("id"),

            "title": (
                work.get("title")
                or "Untitled"
            ),

            "authors": authors,

            "abstract": abstract,

            "publication_year": (
                work.get("publication_year")
            ),

            "citation_count": (
                work.get("cited_by_count", 0)
            ),

            "url": (
                landing_page
                or doi
                or "#"
            ),

            "pdf_url": pdf_url,

            "is_open_access": (
                work.get("open_access", {})
                .get("is_oa", False)
            ),

            "source": "OpenAlex",
        }

        paper["relevance_score"] = calculate_relevance(
            paper,
            topic
        )

        papers.append(paper)

    papers.sort(
        key=lambda paper: (
            paper.get("relevance_score", 0),
            paper.get("citation_count", 0),
        ),
        reverse=True
    )

    return papers[:SEARCH_RESULTS_TO_SHOW]



st.title("📚 Profsistant AI")

st.markdown(
    """
    ### Your AI-powered research assistant

    Search for a research topic and discover relevant academic
    papers to build your reading list.
    """
)



st.subheader("🔎 Find Research Papers")

topic = st.text_input(
    "Enter a research topic",
    placeholder=(
        "e.g. privacy preserving federated learning"
    ),
)

search_button = st.button(
    "Search Papers",
    type="primary"
)

if search_button:

    if not topic.strip():
        st.warning(
            "Please enter a research topic first."
        )

    else:

        with st.spinner(
            "Searching OpenAlex for relevant papers..."
        ):

            try:

                papers = search_openalex(
                    topic.strip()
                )

                st.session_state.search_results = papers
                st.session_state.last_search_topic = (
                    topic.strip()
                )

            except requests.exceptions.RequestException as e:

                st.error(
                    "Unable to search OpenAlex right now."
                )

                st.caption(
                    f"Error: {e}"
                )

            except Exception as e:

                st.error(
                    "Something went wrong while searching."
                )

                st.caption(
                    f"Error: {e}"
                )



papers = st.session_state.search_results

if papers:

    st.divider()

    st.subheader(
        f"📄 Results for "
        f'"{st.session_state.last_search_topic}"'
    )

    st.caption(
        f"Showing the top {len(papers)} relevant papers."
    )


    existing = (
        supabase
        .table("papers")
        .select("openalex_id")
        .eq("user_id", user_id)
        .execute()
    )

    existing_openalex_ids = {
        row["openalex_id"]
        for row in (existing.data or [])
        if row.get("openalex_id")
    }



    for idx, paper in enumerate(papers):

        openalex_id = paper.get("openalex_id")

        with st.container(border=True):


            st.markdown(
                f"### {idx + 1}. {paper['title']}"
            )

          
            metadata = []

            if paper.get("authors"):
                metadata.append(
                    f"**Authors:** {paper['authors']}"
                )

            if paper.get("publication_year"):
                metadata.append(
                    f"**Year:** "
                    f"{paper['publication_year']}"
                )

            metadata.append(
                f"**Citations:** "
                f"{paper.get('citation_count', 0)}"
            )

            st.markdown(
                "  \n".join(metadata)
            )


            abstract = paper.get(
                "abstract",
                ""
            )

            if abstract:

                st.markdown(
                    "**Abstract**"
                )

                if len(abstract) > ABSTRACT_DISPLAY_LENGTH:

                    st.write(
                        abstract[
                            :ABSTRACT_DISPLAY_LENGTH
                        ] + "..."
                    )

                    with st.expander(
                        "Read full abstract"
                    ):

                        st.write(
                            abstract
                        )

                else:

                    st.write(
                        abstract
                    )

            else:

                st.caption(
                    "No abstract available."
                )


            link_columns = st.columns(2)

            with link_columns[0]:

                if paper.get("url") and paper["url"] != "#":

                    st.link_button(
                        "🔗 View Paper",
                        paper["url"]
                    )

            with link_columns[1]:

                if paper.get("pdf_url"):

                    st.link_button(
                        "📄 Open PDF",
                        paper["pdf_url"]
                    )

                elif paper.get("is_open_access"):

                    st.caption(
                        "Open access available"
                    )

            if abstract:

                if st.button(
                    "✨ Summarize with AI",
                    key=f"summary_{openalex_id}_{idx}"
                ):

                    # Keep Gemini input reasonably small.
                    gemini_abstract = abstract[
                        :ABSTRACT_GEMINI_LENGTH
                    ]

                    with st.spinner(
                        "Generating summary..."
                    ):

                        try:

                            prompt = f"""
You are an academic research assistant.

Summarize the following research paper for a
researcher who is exploring this topic:

Research topic:
{st.session_state.last_search_topic}

Paper title:
{paper['title']}

Abstract:
{gemini_abstract}

Provide:

1. A 2-3 sentence summary
2. The main problem being addressed
3. The key approach or methodology
4. The main contribution
5. Why this paper may be useful for someone
   researching the given topic

Keep the explanation concise and easy to understand.
"""

                            response = (
                                gemini_client.models.generate_content(
                                    model="gemini-3.5-flash",
                                    contents=prompt
                                )
                            )

                            st.markdown(
                                "#### 🤖 AI Summary"
                            )

                            st.write(
                                response.text
                            )

                        except Exception as e:

                            st.error(
                                "Unable to generate the summary."
                            )

                            st.caption(
                                f"Error: {e}"
                            )


            st.divider()

            if openalex_id in existing_openalex_ids:

                st.success(
                    "✓ Already in your reading list"
                )

            else:

                if st.button(
                    "➕ Add to Reading List",
                    key=f"add_{openalex_id}_{idx}"
                ):

                    try:

                        add_paper(
                            user_id,
                            paper
                        )


                        existing_openalex_ids.add(
                            openalex_id
                        )

                        st.success(
                            "Added to your reading list!"
                        )

                    except Exception as e:

                        st.error(
                            "Unable to add this paper "
                            "to your reading list."
                        )

                        st.caption(
                            f"Error: {e}"
                        )



elif (
    st.session_state.last_search_topic
    and not papers
):

    st.info(
        "No relevant papers were found. "
        "Try using a broader research topic."
    )



st.divider()

st.caption(
    "Profsistant AI • Powered by OpenAlex and Gemini"
)
