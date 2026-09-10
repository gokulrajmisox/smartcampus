import streamlit as st
import folium
from streamlit_folium import st_folium
from src.logger import logger

def render_map_view(current_map: folium.Map):
    """Renders the Folium interactive map within Streamlit columns."""
    st.subheader("🗺️ Interactive Campus Map")
    
    if not current_map:
        st.warning("Map failed to load. Please verify data files.")
        return None
        
    try:
        map_data = st_folium(
            current_map,
            width=700,
            height=500,
            returned_objects=["last_clicked"]
        )
        return map_data
    except Exception as e:
        logger.error(f"Error rendering interactive map view: {e}", exc_info=True)
        st.error("Error drawing Folium map layer.")
        return None
