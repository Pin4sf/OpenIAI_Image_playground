import streamlit as st
import hmac
import hashlib
import time
from typing import Optional


def check_password(username: str, password: str) -> bool:
    """Verify username and password against stored credentials."""
    # Get credentials from secrets
    credentials = st.secrets.get("credentials", {})

    if username not in credentials:
        return False

    stored_password = credentials[username]
    # Use hmac to prevent timing attacks
    return hmac.compare_digest(password.encode(), stored_password.encode())


def login_user(username: str, password: str) -> bool:
    """Attempt to log in a user and set session state."""
    if check_password(username, password):
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        return True
    return False


def logout_user():
    """Log out the current user."""
    st.session_state["authenticated"] = False
    st.session_state["username"] = None


def is_authenticated() -> bool:
    """Check if the user is authenticated."""
    return st.session_state.get("authenticated", False)


def get_current_user() -> Optional[str]:
    """Get the current authenticated username."""
    return st.session_state.get("username")
