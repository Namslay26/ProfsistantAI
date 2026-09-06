import streamlit as st
from supabase import create_client


# ============================================================
# SUPABASE CLIENT
# ============================================================

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_API_KEY"]
    )


# ============================================================
# ADD PAPER
# ============================================================

def add_paper(user_id, paper):

    return (
        get_supabase()
        .table("papers")
        .insert({
            "user_id": user_id,
            "openalex_id": paper.get("openalex_id"),
            "title": paper.get("title", ""),
            "authors": paper.get("authors", ""),
            "abstract": paper.get("abstract", ""),
            "url": paper.get("url", "#"),
            "source": paper.get("source", "OpenAlex"),
            "labels": paper.get("labels", []),
            "status": paper.get("status", "To Read"),
            "notes": paper.get("notes", ""),
            "publication_year": paper.get("publication_year"),
            "citation_count": paper.get("citation_count", 0),
        })
        .execute()
    )


# ============================================================
# GET USER'S PAPERS
# ============================================================

def get_user_papers(user_id):

    response = (
        get_supabase()
        .table("papers")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


# ============================================================
# GET A SINGLE PAPER
# ============================================================

def get_paper(paper_id, user_id):

    response = (
        get_supabase()
        .table("papers")
        .select("*")
        .eq("id", paper_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )

    return response.data


# ============================================================
# UPDATE PAPER
# ============================================================

def update_paper(paper_id, user_id, updates):

    return (
        get_supabase()
        .table("papers")
        .update(updates)
        .eq("id", paper_id)
        .eq("user_id", user_id)
        .execute()
    )


# ============================================================
# UPDATE PAPER STATUS
# ============================================================

def update_paper_status(paper_id, user_id, status):

    return update_paper(
        paper_id,
        user_id,
        {
            "status": status
        }
    )


# ============================================================
# UPDATE PAPER NOTES
# ============================================================

def update_paper_notes(paper_id, user_id, notes):

    return update_paper(
        paper_id,
        user_id,
        {
            "notes": notes
        }
    )


# ============================================================
# UPDATE PAPER LABELS
# ============================================================

def update_paper_labels(paper_id, user_id, labels):

    return update_paper(
        paper_id,
        user_id,
        {
            "labels": labels
        }
    )


# ============================================================
# DELETE PAPER
# ============================================================

def delete_paper(paper_id, user_id):

    return (
        get_supabase()
        .table("papers")
        .delete()
        .eq("id", paper_id)
        .eq("user_id", user_id)
        .execute()
    )
