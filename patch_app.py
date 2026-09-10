import re
import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Change Page Title and headers
content = content.replace('page_title="AI Campus Navigator"', 'page_title="CampusAI - Smart Campus Copilot"')
content = content.replace('st.title("🗺️ AI Campus Navigator")', 'st.title("🏛️ CampusAI")\n    st.markdown("### One intelligent layer for a more accessible campus.")')
content = content.replace('st.markdown("An interactive routing and pathfinding application utilizing OpenStreetMap XML data, graph search algorithms, and Gemini AI assistance.")', '')

# We need to insert the Global Search and Role Selector somewhere before sidebar rendering.
header_inject = """
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.session_state['user_role'] = st.selectbox("👤 Select Your Role (Workforce Mode)", ["Student", "Faculty", "Visitor", "Security", "Maintenance", "Support Staff"])
    with col2:
        search_query = st.text_input("🔍 Global Smart Search (Buildings, Labs, Facilities)")
        if search_query:
            # Fake search results processing for demo
            st.info(f"Searched for: {search_query}. Ask CampusAI for detailed routes!")
    with col3:
        if st.button("🚨 EMERGENCY MODE", type="primary", use_container_width=True):
            st.session_state['emergency_mode'] = True
            st.warning("EMERGENCY MODE ACTIVATED: Routing to nearest Medical Center...")
            # Automatically trigger route to Medical Center
            if 'Medical Center' in pathfinder.POIS:
                result = pathfinder.find_path(list(pathfinder.POIS.keys())[0], "Medical Center", "A*")
                st.session_state['current_map'] = result['map']
                st.rerun()

    st.markdown("---")
"""

# Insert right after st.markdown("---") in the header block
content = content.replace('st.markdown("---")', 'st.markdown("---")\n' + header_inject, 1) # Only first occurrence

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched app.py")
