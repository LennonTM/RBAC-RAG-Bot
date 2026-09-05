import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Internal Chatbot", page_icon="💬")


def login(username: str, password: str) -> dict | None:
    response = requests.get(f"{API_URL}/login", auth=(username, password))
    if response.status_code == 200:
        return response.json()
    return None


def send_message(username: str, password: str, message: str) -> str:
    response = requests.post(
        f"{API_URL}/chat",
        auth=(username, password),
        params={"message": message},
    )
    response.raise_for_status()
    return response.json().get("hello", "")


if "auth" not in st.session_state:
    st.session_state.auth = None
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.auth is None:
    st.title("Log in")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        result = login(username, password)
        if result is None:
            st.error("Invalid credentials.")
        else:
            st.session_state.auth = {
                "username": username,
                "password": password,
                "role": result["role"],
            }
            st.rerun()
else:
    auth = st.session_state.auth
    st.sidebar.write(f"Logged in as **{auth['username']}** ({auth['role']})")
    if st.sidebar.button("Log out"):
        st.session_state.auth = None
        st.session_state.messages = []
        st.rerun()

    st.title("Internal Chatbot")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask something..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        try:
            reply = send_message(auth["username"], auth["password"], prompt)
        except requests.HTTPError as e:
            reply = f"Error: {e}"

        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)
