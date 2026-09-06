import time

import streamlit as st
from google import genai

MODEL = "gemini-3.5-flash"


def _session_key():
    return (st.session_state.get("user_gemini_api_key") or "").strip()


def get_ai_mode():
    return st.session_state.get("ai_provider_mode", "byok")


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


@st.cache_resource(show_spinner=False)
def _create_gemini_client(api_key):
    return genai.Client(api_key=api_key)


def get_gemini_client():
    """Return a reusable client whose transport stays open across reruns."""
    return _create_gemini_client(get_gemini_api_key())


def generate_content(contents, model=MODEL, attempts=3):
    """Generate content, retrying temporary Gemini capacity and rate-limit errors."""
    for attempt in range(attempts):
        try:
            return get_gemini_client().models.generate_content(
                model=model,
                contents=contents,
            )
        except Exception as exc:
            code = getattr(exc, "code", None)
            if code not in {429, 500, 502, 503, 504} or attempt == attempts - 1:
                raise
            time.sleep(2**attempt)


def has_user_key():
    return bool(_session_key())


def clear_user_key():
    st.session_state.pop("user_gemini_api_key", None)


def validate_user_key(key):
    """Make one small Gemini request to verify that a supplied key works."""
    key = (key or "").strip()
    if not key:
        return False, "Enter a Gemini API key first."

    client = None
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
        code = getattr(exc, "code", None)
        if code in {429, 500, 502, 503, 504}:
            return True, (
                "The key was accepted, but Gemini is temporarily busy. "
                "You can continue and retry generation shortly."
            )
        return False, f"Gemini rejected the key: {exc}"
    finally:
        if client is not None:
            client.close()
