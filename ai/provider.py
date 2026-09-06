import streamlit as st
from google import genai

MODEL = "gemini-3.5-flash"


def _session_key():
    return (st.session_state.get("user_gemini_api_key") or "").strip()


def get_ai_mode():
    return st.session_state.get("ai_provider_mode", "profsistant")


def set_ai_mode(mode):
    if mode not in {"profsistant", "byok"}:
        raise ValueError("Unsupported AI provider mode")
    st.session_state.ai_provider_mode = mode


def get_gemini_api_key():
    """Return the key for the current session without persisting a user key."""
    if get_ai_mode() == "byok":
        key = _session_key()
        if not key:
            raise RuntimeError(
                "Add your Gemini API key in Settings, or switch back to Profsistant AI."
            )
        return key

    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception as exc:
        raise RuntimeError(
            "Profsistant's Gemini key is not configured. Add GEMINI_API_KEY to Streamlit secrets "
            "or use your own key in Settings."
        ) from exc


def get_gemini_client():
    return genai.Client(api_key=get_gemini_api_key())


def has_user_key():
    return bool(_session_key())


def clear_user_key():
    st.session_state.pop("user_gemini_api_key", None)


def validate_user_key(key):
    """Make one small Gemini request to verify that a supplied key works."""
    key = (key or "").strip()
    if not key:
        return False, "Enter a Gemini API key first."

    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=MODEL,
            contents="Reply with exactly: OK",
        )
        if not getattr(response, "text", None):
            return False, "Gemini responded without text. The key may not have access to this model."
        return True, "Gemini API key works."
    except Exception as exc:
        return False, f"Gemini rejected the key: {exc}"
