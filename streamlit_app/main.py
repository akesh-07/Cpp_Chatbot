import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="C++ Assistant Chatbot",
    page_icon="🤖",
    layout="wide"
)

# --- App Title ---
st.title("🤖 C++ Competitive Programming Assistant")
st.caption("A LangGraph-powered chatbot to help you write, test, and debug C++ code.")

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": "Hello! I am your C++ assistant. How can I help you today? You can ask me to run C++ code for you."}
    ]

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input Handling ---
if prompt := st.chat_input("What would you like to do?"):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- API Communication ---
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        api_url = "http://127.0.0.1:8000/chat"

        # Send the entire message history (excluding the latest user prompt)
        # The welcome message is the first item, so we skip it by slicing `[1:]`
        history = st.session_state.messages[:-1]

        payload = {
            "message": prompt,
            "history": history
        }

        try:
            with requests.post(api_url, json=payload, stream=True) as response:
                # Raise an exception for bad status codes (4xx or 5xx)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=None):
                    if chunk:
                        decoded_chunk = chunk.decode('utf-8')
                        full_response += decoded_chunk
                        message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to the backend: {e}")