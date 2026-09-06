import streamlit as st

from supabase import create_client


# ============================================================
# SUPABASE SETUP
# ============================================================

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_API_KEY"]
    )


supabase = get_supabase()


# ============================================================
# LOGIN / SIGNUP
# ============================================================

def login():

    st.title("🔐 Login to Profsistant")

    email = st.text_input(
        "Email",
        key="auth_email"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="auth_password"
    )

    action = st.radio(
        "Action",
        ["Login", "Sign Up"]
    )

    if st.button("Submit", type="primary"):

        if not email or not password:
            st.error(
                "Please enter your email and password."
            )
            return

        try:

            # =================================================
            # LOGIN
            # =================================================

            if action == "Login":

                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                if response.user and response.session:

                    # Store user information
                    st.session_state.user = response.user

                    # Store session information
                    st.session_state.supabase_session = (
                        response.session
                    )

                    # Make sure the Supabase client also has
                    # the authenticated session.
                    supabase.auth.set_session(
                        response.session.access_token,
                        response.session.refresh_token
                    )

                    st.success(
                        "✅ Logged in successfully!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Login failed. Please check your credentials."
                    )


            # =================================================
            # SIGN UP
            # =================================================

            else:

                response = supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })

                if response.user:

                    # -------------------------------------------------
                    # If email confirmation is disabled, Supabase
                    # returns an active session immediately.
                    # -------------------------------------------------

                    if response.session:

                        st.session_state.user = response.user

                        st.session_state.supabase_session = (
                            response.session
                        )

                        supabase.auth.set_session(
                            response.session.access_token,
                            response.session.refresh_token
                        )

                        st.success(
                            "✅ Account created successfully!"
                        )

                        st.rerun()

                    else:

                        st.success(
                            "✅ Account created!"
                        )

                        st.info(
                            "Please check your email and confirm "
                            "your account before logging in."
                        )

                else:

                    st.error(
                        "Could not create the account."
                    )

        except Exception as e:

            st.error(
                f"Authentication failed: {e}"
            )


# ============================================================
# GET CURRENT USER ID
# ============================================================

def get_user_id():

    if (
        "user" in st.session_state
        and st.session_state.user
    ):
        return st.session_state.user.id

    return None
