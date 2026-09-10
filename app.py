import streamlit as st
import pandas as pd
import folium
import os
from src.pathfinding import CampusPathfinder, OSMDataLoadError, PathNotFoundError
from src.ai_assistant import GeminiAssistant
from src.ui.sidebar import render_sidebar
from src.ui.map_viewer import render_map_view
from src.ui.comparison import render_algorithm_comparison, render_heuristic_comparison
from src.logger import logger

# Page configuration
st.set_page_config(
    page_title="AI Campus Navigator",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize engines
@st.cache_resource
def initialize_pathfinder():
    try:
        return CampusPathfinder("attached_assets/map_1758707724808.osm")
    except OSMDataLoadError as e:
        logger.critical(f"Critical initialization error: {e}")
        st.error(f"Fatal Error: Could not parse OSM graph map. Detail: {e}")
        return None

@st.cache_resource
def initialize_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except:
            pass
    return GeminiAssistant(api_key=api_key)

def main():
    logger.info("Starting AI Campus Navigator Streamlit runtime...")
    
    pathfinder = initialize_pathfinder()
    if not pathfinder:
        st.stop()
        
    gemini = initialize_gemini()
    
    # Header block
    st.title("🗺️ AI Campus Navigator")
    st.markdown("An interactive routing and pathfinding application utilizing OpenStreetMap XML data, graph search algorithms, and Gemini AI assistance.")
    st.markdown("---")
    
    # Render Sidebar and retrieve actions
    sidebar_actions = render_sidebar(pathfinder, gemini)
    
    # State handling variables
    run_pathfinding = sidebar_actions["run_pathfinding"]
    start_location = sidebar_actions["start"]
    end_location = sidebar_actions["end"]
    algorithm = sidebar_actions["algorithm"]
    ai_triggered = sidebar_actions["ai_triggered_path"]
    
    # Core state initialization
    if 'current_map' not in st.session_state:
        st.session_state['current_map'] = pathfinder.create_base_map()
        st.session_state['path_metrics'] = None
        st.session_state['algorithm_used'] = None
        
    # Check if AI triggered map update
    if ai_triggered:
        if ai_triggered["action"] == "route":
            try:
                result = pathfinder.find_path(ai_triggered["start"], ai_triggered["end"], "A*")
                st.session_state['current_map'] = result['map']
                st.session_state['path_metrics'] = result['metrics']
                st.session_state['algorithm_used'] = "A* (via AI)"
                st.rerun()
            except Exception as e:
                logger.error(f"Error drawing AI triggered route: {e}")
        elif ai_triggered["action"] == "highlight":
            try:
                # Highlight single point
                m = pathfinder.create_base_map()
                latlon = pathfinder.POIS[ai_triggered["location"]]
                folium.Marker(
                    latlon,
                    popup=f"Highlighted: {ai_triggered['location']}",
                    icon=folium.Icon(color="orange", icon="star")
                ).add_to(m)
                st.session_state['current_map'] = m
                st.session_state['path_metrics'] = None
                st.rerun()
            except Exception as e:
                logger.error(f"Error highlighting single POI via AI: {e}")

    # Handle standard pathfinding button trigger
    if run_pathfinding:
        try:
            with st.spinner(f"Computing route using {algorithm}..."):
                result = pathfinder.find_path(start_location, end_location, algorithm)
                st.session_state['current_map'] = result['map']
                st.session_state['path_metrics'] = result['metrics']
                st.session_state['algorithm_used'] = algorithm
                st.success(f"✅ Route successfully generated!")
        except PathNotFoundError as e:
            logger.warning(f"Routing logic failure: {e}")
            st.error(f"❌ Route calculation error: {e}")
        except Exception as e:
            logger.error(f"Unexpected pathfinder failure: {e}", exc_info=True)
            st.error(f"❌ Unexpected routing calculation failure.")

    # Main grid view layout
    col_map, col_metrics = st.columns([2, 1])
    
    with col_map:
        render_map_view(st.session_state['current_map'])
        
    with col_metrics:
        st.subheader("📋 Route Metrics")
        
        metrics = st.session_state['path_metrics']
        if metrics:
            st.metric("🚶 Algorithm Executed", st.session_state['algorithm_used'])
            st.metric("📏 Computed Distance", f"{metrics['distance']:.1f} meters")
            st.metric("⏱️ Estimated Walk Time", f"{metrics['time']:.2f} minutes")
            st.metric("🔍 Graph Nodes Explored", f"{metrics['nodes_explored']:,}")
            
            st.subheader("🏢 Location Details")
            start_info = pathfinder.get_location_info(metrics['start_location'])
            end_info = pathfinder.get_location_info(metrics['end_location'])
            
            st.write("**Start Location:**")
            st.info(f"📍 {start_info['name']} ({start_info['type']})\n📍 Coordinates: {start_info['coordinates']}")
            
            st.write("**Destination:**")
            st.info(f"🏁 {end_info['name']} ({end_info['type']})\n📍 Coordinates: {end_info['coordinates']}")
        else:
            st.info("Choose a start and end location on the sidebar to find a path, or talk to the AI Assistant.")

    # Render audit panels if requested
    if sidebar_actions["run_comparison"]:
        render_algorithm_comparison(pathfinder)
        
    if sidebar_actions["run_heuristic_comparison"]:
        render_heuristic_comparison(pathfinder)

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>🎓 Professional Campus Pathfinding Engine | Powered by OSMnx, NetworkX, and Google Gemini AI</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled Streamlit thread exception: {e}", exc_info=True)
        st.error("Platform encountered an unhandled system thread failure.")

