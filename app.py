import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="CampusAI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
try:
    with open('assets/style.css', 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except Exception as e:
    pass

from src.pathfinding import CampusPathfinder, OSMDataLoadError
from src.ai_assistant import GeminiAssistant
from src.ui.sidebar import render_sidebar
from src.ui.home import render_home
from src.ui.navigation import render_navigation
from src.ui.chat import render_chat
from src.ui.facilities import render_facilities
from src.logger import logger

# Initialize engines
@st.cache_resource
def initialize_pathfinder():
    try:
        return CampusPathfinder("attached_assets/sathyabama_small.osm")
    except OSMDataLoadError as e:
        logger.critical(f"Critical initialization error: {e}")
        st.error(f"Fatal Error: Could not parse OSM graph map. Detail: {e}")
        return None

@st.cache_resource
def initialize_ai():
    return GeminiAssistant()

pathfinder = initialize_pathfinder()
gemini = initialize_ai()

# Routing state
if 'current_view' not in st.session_state:
    st.session_state.current_view = "Home"
if 'nav_start' not in st.session_state:
    st.session_state.nav_start = None
if 'nav_end' not in st.session_state:
    st.session_state.nav_end = None

# Global state
if 'user_role' not in st.session_state:
    st.session_state.user_role = "Student"
if 'accessibility_mode' not in st.session_state:
    st.session_state.accessibility_mode = False

# Render Sidebar
render_sidebar()

# Route to correct view
if st.session_state.current_view == "Home":
    render_home(pathfinder, gemini)
elif st.session_state.current_view == "Navigate":
    render_navigation(pathfinder)
elif st.session_state.current_view == "Ask CampusAI":
    render_chat(gemini)
elif st.session_state.current_view == "Facilities":
    render_facilities(pathfinder)
