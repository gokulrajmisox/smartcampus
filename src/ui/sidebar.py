import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; color: #0F172A; margin-bottom: 2rem;'>🏛️ CampusAI</h2>", unsafe_allow_html=True)

        # Navigation
        views = ["Home", "Navigate", "Ask CampusAI", "Facilities"]

        for view in views:
            if st.button(view, key=f"nav_{view}", use_container_width=True, type="primary" if st.session_state.current_view == view else "secondary"):
                st.session_state.current_view = view
                st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")

        # Role Selector
        st.markdown("### Profile")
        st.session_state.user_role = st.selectbox(
            "Viewing as",
            ["Student", "Faculty", "Visitor", "Security", "Maintenance", "Support Staff"],
            index=["Student", "Faculty", "Visitor", "Security", "Maintenance", "Support Staff"].index(st.session_state.user_role)
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Emergency Button
        st.markdown('<div class="emergency-btn">', unsafe_allow_html=True)
        if st.button("🚨 Emergency", use_container_width=True):
            st.session_state.current_view = "Navigate"
            # Set navigation directly to Medical Center
            locations = list(st.session_state.get('locations_cache', ["Main Gate"]))
            st.session_state.nav_start = locations[0] if locations else None
            st.session_state.nav_end = "Medical Center"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
