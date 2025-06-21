# pages/1_📚_Reading_List.py

import streamlit as st


st.title("📚 Your Research Reading List")

# --- Init session states ---
if "reading_list" not in st.session_state:
    st.session_state.reading_list = []

if "progress" not in st.session_state:
    st.session_state.progress = []

# 🧠 Fix: Ensure progress list is same length as reading_list
while len(st.session_state.progress) < len(st.session_state.reading_list):
    st.session_state.progress.append({"status": "To Read", "notes": ""})
while len(st.session_state.progress) > len(st.session_state.reading_list):
    st.session_state.progress.pop()

# --- Display Reading List ---
if not st.session_state.reading_list:
    st.info("Your reading list is empty. Add papers below or from the Home page.")
else:
    statuses = ["To Read", "Reading", "Done"]
    for idx, paper in enumerate(st.session_state.reading_list):
        st.markdown("---")
        st.subheader(f"{idx+1}. {paper['title']}")
        st.markdown(f"**Authors:** {paper['authors']}")
        st.markdown(f"📌 **Source:** {paper.get('source', 'Unknown')} | 🏷️ Labels: {', '.join(paper.get('labels', [])) or 'None'}")
        st.markdown(f"[🔗 View Paper]({paper['url']})")
        st.markdown(f"📄 **Abstract:** {paper['abstract']}")

        # --- Status ---
        progress = st.session_state.progress[idx]
        current_status = progress.get("status", "To Read")
        progress["status"] = st.selectbox(
            "📘 Status", statuses, index=statuses.index(current_status), key=f"status_{idx}"
        )

        # --- Notes ---
        current_notes = progress.get("notes", "")
        progress["notes"] = st.text_area("📝 Notes", value=current_notes, key=f"notes_{idx}")

        # --- Remove ---
        if st.button(f"🗑️ Remove Paper #{idx+1}", key=f"remove_{idx}"):
            st.session_state.reading_list.pop(idx)
            st.session_state.progress.pop(idx)
            st.experimental_rerun()

# --- Add Custom Paper Form (Moved to Bottom) ---
st.markdown("---")
st.subheader("➕ Add a Custom Paper")

with st.form("add_paper_form"):
    title = st.text_input("Title")
    authors = st.text_input("Authors")
    abstract = st.text_area("Abstract")
    url = st.text_input("Optional URL")
    source = st.selectbox("📌 Source", ["Manual", "Google Scholar", "Conference X", "Arxiv", "Advisor"])
    labels = st.multiselect("🏷️ Labels", ["Survey", "Theoretical", "Empirical", "Review", "Application"])

    submit = st.form_submit_button("Add to Reading List")

if submit:
    if title and authors and abstract:
        new_paper = {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "url": url if url else "#",
            "source": source,
            "labels": labels
        }
        st.session_state.reading_list.append(new_paper)
        st.session_state.progress.append({"status": "To Read", "notes": ""})
        st.success("✅ Paper added!")
        st.experimental_rerun()
    else:
        st.warning("Please fill in the title, authors, and abstract.")
