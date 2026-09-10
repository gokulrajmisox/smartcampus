import streamlit as st

def render_chat(gemini):
    st.markdown("<h2>💬 Ask CampusAI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B;'>Your intelligent campus assistant</p>", unsafe_allow_html=True)

    if not gemini:
        st.warning("AI Engine offline. Operating in fallback mode.")

    if 'messages' not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you navigate the campus today?"}]
        st.session_state.ai_context = {"conversation_history": []}

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🏛️" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
            # If the message contains an action button
            if "action_route" in msg:
                if st.button("Navigate →", key=f"nav_{msg['action_route']['start']}_{msg['action_route']['end']}"):
                    st.session_state.nav_start = msg['action_route']['start']
                    st.session_state.nav_end = msg['action_route']['end']
                    st.session_state.current_view = "Navigate"
                    st.rerun()

    # Pre-fill query if coming from Home screen
    initial_query = st.session_state.get('initial_chat_query', None)

    user_query = st.chat_input("Ask about places, rules, or directions...")

    # Process query
    active_query = initial_query or user_query

    if active_query:
        if initial_query:
            st.session_state.initial_chat_query = None # clear it

        st.session_state.messages.append({"role": "user", "content": active_query})
        with st.chat_message("user", avatar="👤"):
            st.markdown(active_query)

        with st.chat_message("assistant", avatar="🏛️"):
            with st.spinner("Thinking..."):
                role = st.session_state.get('user_role', 'Student')

                if gemini:
                    response, updated_context = gemini.get_response(active_query, st.session_state.ai_context, role=role)
                else:
                    from src.ai_assistant import GeminiAssistant
                    fallback = GeminiAssistant(api_key="")
                    response, updated_context = fallback.get_response(active_query, st.session_state.ai_context, role=role)

                st.session_state.ai_context = updated_context

                msg_data = {"role": "assistant", "content": response["text"]}

                # Check for routing intent
                if response.get("show_route") and response.get("start") and response.get("end"):
                    msg_data["action_route"] = {
                        "start": response["start"],
                        "end": response["end"]
                    }

                st.session_state.messages.append(msg_data)
                st.markdown(response["text"])
                if "action_route" in msg_data:
                    if st.button("Navigate →", key="nav_immediate"):
                        st.session_state.nav_start = msg_data['action_route']['start']
                        st.session_state.nav_end = msg_data['action_route']['end']
                        st.session_state.current_view = "Navigate"
                        st.rerun()
