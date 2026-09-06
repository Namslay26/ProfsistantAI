import streamlit as st
from auth import login
from ai.provider import (
    clear_user_key,
    get_ai_mode,
    has_user_key,
    set_ai_mode,
    validate_user_key,
)
from ui import apply_theme, sidebar, page_header

apply_theme()
sidebar()

if "user" not in st.session_state:
    login()
    st.stop()

page_header(
    "SETTINGS",
    "Choose how Profsistant uses AI",
    "Use Profsistant's Gemini access or bring your own Gemini API key. Your personal key is kept only in this browser session and is not saved to your Profsistant account.",
)

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)

mode = st.segmented_control(
    "AI provider",
    options=["Profsistant AI", "My Gemini API key"],
    default="My Gemini API key" if get_ai_mode() == "byok" else "Profsistant AI",
    key="settings_ai_mode",
)

if mode == "My Gemini API key":
    set_ai_mode("byok")

    st.markdown(
        '<div class="callout"><strong>Bring Your Own Key</strong><br>'
        '<span class="muted">Gemini usage is sent through Profsistant using the key you provide. '
        'The key is kept in your Streamlit session only and is not written to Supabase.</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Gemini API key")
    st.caption("Treat this key like a password. Never share it publicly or commit it to Git.")

    existing = st.session_state.get("user_gemini_api_key", "")
    entered = st.text_input(
        "Gemini API key",
        value=existing,
        type="password",
        placeholder="Paste your Gemini API key",
        label_visibility="collapsed",
        key="gemini_key_input",
    )

    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        if st.button("Test & save key", type="primary"):
            key = entered.strip()
            ok, message = validate_user_key(key)
            if ok:
                st.session_state.user_gemini_api_key = key
                st.session_state.ai_provider_mode = "byok"
                st.success(message)
            else:
                st.error(message)
    with c2:
        if st.button("Clear key"):
            clear_user_key()
            st.session_state.ai_provider_mode = "profsistant"
            st.session_state.pop("gemini_key_input", None)
            st.toast("Your Gemini key was cleared from this session.")
            st.rerun()
    with c3:
        if has_user_key():
            st.success("✓ Key connected")
        else:
            st.info("No key connected")

    st.markdown("### What this means")
    st.markdown(
        "- **Your Gemini quota:** used when your key is active.\n"
        "- **Profsistant storage:** your key is **not** stored in Supabase.\n"
        "- **Session lifetime:** clearing the session/logging out removes the in-memory key.\n"
        "- **OpenAlex:** literature search is separate and does not use your Gemini quota."
    )

else:
    set_ai_mode("profsistant")
    st.markdown(
        '<div class="callout"><strong>Profsistant AI</strong><br>'
        '<span class="muted">Profsistant supplies the Gemini API access for this session. '
        'You do not need to enter a key.</span></div>',
        unsafe_allow_html=True,
    )
    if has_user_key():
        st.caption("You have a Gemini key stored in this session. It will not be used while Profsistant AI is selected.")

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
st.subheader("About API keys")
st.markdown(
    "Google recommends treating Gemini API keys like passwords and not exposing them in client-side production applications. "
    "In this Streamlit version, your entered key is sent to the Profsistant server so the server can call Gemini on your behalf. "
    "For a future Next.js production architecture, keep provider calls behind a server-side API route."
)
st.link_button("Read Google's Gemini API key guidance ↗", "https://ai.google.dev/gemini-api/docs/api-key")
