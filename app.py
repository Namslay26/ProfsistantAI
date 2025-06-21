import streamlit as st 
from scholarly import scholarly
from google import genai

# Configuring gemini API
api_key = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=api_key)


# Session state for reading list
if "reading_list" not in st.session_state:
    st.session_state.reading_list = []

st.set_page_config(page_title="Profsistant AI", page_icon="🎓", layout="wide")
st.title("📚 Profsistant - Your Research Kick-Starter")
st.markdown(
    """
    Profsistant is an AI-powered research assistant designed to help you kick-start your academic journey. 
    It provides quick access to scholarly articles, summaries, and insights.
    """
)
#input 
topic = st.text_input("Enter your research topic or area of interest:")

if topic:
    st.write("🔍 Searching for top papers...")
    search_results = scholarly.search_pubs(topic)

    papers = []
    for i in range(5):  # Top 5 papers
        try:
            paper = next(search_results)
            papers.append({
                "title": paper.get("bib", {}).get("title", "No title"),
                "abstract": paper.get("bib", {}).get("abstract", "No abstract available."),
                "authors": paper.get("bib", {}).get("author", "Unknown"),
                "url": paper.get("pub_url", "#")
            })
        except StopIteration:
            break

    st.write("📝 Found papers:")
    for idx, paper in enumerate(papers):
        st.subheader(f"{idx+1}. {paper['title']}")
        st.markdown(f"**Authors:** {paper['authors']}")
        st.markdown(f"[🔗 View Paper]({paper['url']})")
        st.markdown(f"📄 **Abstract:** {paper['abstract']}")

        if st.button(f"Summarize #{idx+1}", key=f"summarize_{idx}"):
            with st.spinner("Using Gemini to summarize..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents= f"""
                    Summarize the following research abstract into 3 bullet points. Then, suggest one possible research direction or idea a student could explore based on it.
 
                    Abstract:
                    {paper['abstract']}
                    """
                )
                st.markdown("### ✨ Summary + Suggested Research Direction:")
                st.markdown(response.text)
        if st.button(f"Add to Reading List #{idx+1}", key=f"add_{idx}"):
            st.session_state.reading_list.append(paper)
            st.success("✅ Added to reading list!")