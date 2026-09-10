import streamlit as st

def render_facilities(pathfinder):
    st.markdown("<h2>🏢 Campus Directory</h2>", unsafe_allow_html=True)

    if not pathfinder or not hasattr(pathfinder, 'locations_data'):
        st.warning("Facilities data not available.")
        return

    search_query = st.text_input("🔍 Search facilities...", placeholder="e.g. Library, Lab, Food", label_visibility="collapsed")

    locations = pathfinder.locations_data.values()

    # Filter locations
    if search_query:
        locations = [loc for loc in locations if search_query.lower() in loc['name'].lower() or search_query.lower() in loc.get('description', '').lower() or search_query.lower() in loc.get('type', '').lower()]

    st.markdown("<br>", unsafe_allow_html=True)

    for loc in locations:
        st.markdown('<div class="card-style" style="margin-bottom: 1rem;">', unsafe_allow_html=True)
        col_info, col_action = st.columns([8, 2])
        with col_info:
            st.markdown(f"**{loc['name']}**")
            meta = []
            if loc.get('building'): meta.append(loc['building'])
            if loc.get('floor'): meta.append(f"Floor {loc['floor']}")
            if loc.get('accessibility', {}).get('wheelchair'): meta.append("♿ Accessible")

            st.markdown(f"<span style='color: #64748B; font-size: 0.9rem;'>{' · '.join(meta)}</span>", unsafe_allow_html=True)
            if loc.get('description'):
                st.markdown(f"<p style='font-size: 0.9rem; margin-top: 0.5rem;'>{loc['description']}</p>", unsafe_allow_html=True)

        with col_action:
            if st.button("Map →", key=f"fac_{loc['name']}", use_container_width=True):
                st.session_state.nav_end = loc['name']
                st.session_state.current_view = "Navigate"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if not locations:
        st.markdown("<div style='text-align: center; padding: 3rem; color: #64748B;'>We couldn't find that location.</div>", unsafe_allow_html=True)
