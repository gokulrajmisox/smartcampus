import streamlit as st
from streamlit_folium import st_folium
import folium

def render_navigation(pathfinder):
    if not pathfinder:
        st.error("Map engine offline.")
        return

    st.markdown("<h2>📍 Navigation</h2>", unsafe_allow_html=True)

    locations = list(pathfinder.POIS.keys())

    # Setup session state for nav selection
    if st.session_state.get('nav_start') not in locations:
        st.session_state.nav_start = locations[0] if locations else None
    if st.session_state.get('nav_end') not in locations:
        st.session_state.nav_end = locations[1] if len(locations) > 1 else None

    # Layout: Route Panel (Left, 30%), Map (Right, 70%)
    col_panel, col_map = st.columns([3, 7])

    with col_panel:
        st.markdown('<div class="card-style">', unsafe_allow_html=True)
        st.session_state.nav_start = st.selectbox("From", locations, index=locations.index(st.session_state.nav_start) if st.session_state.nav_start else 0)
        st.session_state.nav_end = st.selectbox("To", locations, index=locations.index(st.session_state.nav_end) if st.session_state.nav_end else 1)

        st.markdown("<br>", unsafe_allow_html=True)

        st.session_state.accessibility_mode = st.toggle("♿ Accessible Route", value=st.session_state.get('accessibility_mode', False))

        st.markdown("<br>", unsafe_allow_html=True)

        run_route = st.button("Route →", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Route Output Area
        route_output_placeholder = st.empty()

    with col_map:
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        map_placeholder = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)

    # Initial Map or Route
    current_map = None
    metrics = None

    # If emergency triggered, run immediately. Or if run_route clicked.
    if run_route or (st.session_state.nav_start and st.session_state.nav_end and st.session_state.get('emergency_mode', False)):
        if st.session_state.nav_start == st.session_state.nav_end:
            st.warning("Start and End locations are the same.")
        else:
            with st.spinner("Calculating route..."):
                try:
                    # We hardcode algorithm to A* as requested
                    result = pathfinder.find_path(st.session_state.nav_start, st.session_state.nav_end, "A*", accessibility_mode=st.session_state.accessibility_mode)
                    current_map = result['map']
                    metrics = result['metrics']
                except Exception as e:
                    st.error(f"Error calculating route: {e}")
        st.session_state.emergency_mode = False # reset

    if not current_map:
        # Render center map with all POI markers
        current_map = pathfinder.create_base_map()

    with map_placeholder:
        st_folium(current_map, use_container_width=True, height=600, returned_objects=[])

    if metrics:
        with route_output_placeholder.container():
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="card-style">', unsafe_allow_html=True)
            st.markdown(f"### {st.session_state.nav_end}")
            st.markdown(f"**{metrics['distance']}** &middot; **{metrics['time']}**")

            if st.session_state.accessibility_mode:
                st.markdown("♿ **Accessible route ON**", unsafe_allow_html=True)

            st.markdown("---")
            # Step timeline mockup
            st.markdown(f"1. **{st.session_state.nav_start}**")
            st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;*Follow highlighted path on map*")
            st.markdown(f"2. **{st.session_state.nav_end}**")
            st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;*Arrive at destination*")
            st.markdown('</div>', unsafe_allow_html=True)
