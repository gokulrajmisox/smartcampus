import streamlit as st

def render_home(pathfinder, gemini):
    # Store locations in session state for cross-referencing
    if 'locations_cache' not in st.session_state and pathfinder:
        st.session_state.locations_cache = list(pathfinder.POIS.keys())

    st.markdown("<br><br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.markdown(f"<h1 style='text-align: center; font-size: 3rem; margin-bottom: 0.5rem;'>Good {'morning' if True else 'evening'}.</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center; color: #64748B; font-weight: 400; margin-bottom: 3rem;'>Where do you need to go?</h3>", unsafe_allow_html=True)

        # Command Bar
        search_query = st.text_input("Ask anything about your campus...", placeholder="e.g. Where is the CSE Lab?", label_visibility="collapsed")

        if search_query:
            st.session_state.current_view = "Ask CampusAI"
            st.session_state.initial_chat_query = search_query
            st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)

        # Quick Actions
        q_col1, q_col2, q_col3, q_col4 = st.columns(4)

        with q_col1:
            if st.button("📍 Navigate", use_container_width=True):
                st.session_state.current_view = "Navigate"
                st.rerun()
        with q_col2:
            if st.button("💬 Ask CampusAI", use_container_width=True):
                st.session_state.current_view = "Ask CampusAI"
                st.rerun()
        with q_col3:
            if st.button("🏢 Find Facility", use_container_width=True):
                st.session_state.current_view = "Facilities"
                st.rerun()
        with q_col4:
            if st.button("♿ Accessible Route", use_container_width=True):
                st.session_state.accessibility_mode = True
                st.session_state.current_view = "Navigate"
                st.rerun()

        st.markdown("<br><br><hr>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 0.9rem;'>CampusAI – Inclusive Smart Campus Copilot</p>", unsafe_allow_html=True)
