import streamlit as st
from typing import Dict, Any, Optional
from src.logger import logger

def render_sidebar(pathfinder, gemini) -> Dict[str, Any]:
    """Renders the Streamlit sidebar controls and chatbot interface."""
    interaction = {
        "start": None,
        "end": None,
        "algorithm": None,
        "run_pathfinding": False,
        "run_comparison": False,
        "run_heuristic_comparison": False,
        "ai_triggered_path": None
    }
    
    with st.sidebar:
        st.header("🎯 Route Planning")
        
        # Safe checks
        if not pathfinder:
            st.error("Pathfinder engine offline.")
            return interaction
            
        locations = list(pathfinder.POIS.keys())
        start_location = st.selectbox("📍 Start Location", locations, index=0)
        end_location = st.selectbox("🏁 End Location", locations, index=1)
        
        algorithm = st.selectbox(
            "Choose Algorithm",
            ["BFS", "DFS", "UCS", "A*", "A* (Euclidean)", "A* (Manhattan)", "A* (Combined)"],
            index=3,
            help="Select the pathfinding algorithm to use. A* variants use different heuristics."
        )
        
        run_pathfinding = st.button("🚀 Find Path", type="primary", use_container_width=True)
        
        st.markdown("---")
        
        st.subheader("📊 Performance Audits")
        col_a, col_b = st.columns(2)
        run_comparison = False
        run_heuristic_comparison = False
        
        with col_a:
            if st.button("🔬 Compare Algos", use_container_width=True):
                run_comparison = True
        with col_b:
            if st.button("🎯 Heuristics", use_container_width=True):
                run_heuristic_comparison = True
        
        st.markdown("---")
        
        st.subheader("🤖 AI Assistant")
        if not gemini:
            st.warning("AI Assistant running in static/offline fallback mode (API Key not set).")
            
        # Chat log session state init
        if 'messages' not in st.session_state:
            st.session_state.messages = []
            
        # Limit chat logs height in sidebar
        chat_container = st.container(height=300)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        user_query = st.chat_input("Ask about campus POIs/routes...")
        ai_triggered_path = None
        
        if user_query:
            # Append user message
            st.session_state.messages.append({"role": "user", "content": user_query})
            
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(user_query)
            
            # Request response from gemini core assistant
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("🤔 Analyzing..."):
                        try:
                            if 'ai_context' not in st.session_state:
                                st.session_state.ai_context = {
                                    'last_location': None,
                                    'last_query_type': None,
                                    'conversation_history': []
                                }
                            
                            # Run assistant
                            if gemini:
                                response, updated_context = gemini.get_response(user_query, st.session_state.ai_context)
                            else:
                                # Safe static fallback assistant if gemini object is None
                                from src.ai_assistant import GeminiAssistant
                                fallback_gemini = GeminiAssistant(api_key="")
                                response, updated_context = fallback_gemini.get_response(user_query, st.session_state.ai_context)
                                
                            st.session_state.ai_context = updated_context
                            
                            # Process potential route actions from the query
                            query_locations = pathfinder.extract_locations(user_query)
                            
                            if response.get("show_route") and len(query_locations) >= 2:
                                ai_triggered_path = {
                                    "action": "route",
                                    "start": response["start"],
                                    "end": response["end"]
                                }
                                # Append details dynamically to chatbot layout
                                route_info = f"\n\n🗺️ **Route details updated on the main map above.**"
                                response["text"] += route_info
                            elif len(query_locations) == 1:
                                ai_triggered_path = {
                                    "action": "highlight",
                                    "location": query_locations[0]
                                }
                                response["text"] += f"\n\n📍 **Highlighting {query_locations[0]} on the main map.**"
                                
                            st.markdown(response["text"])
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response["text"]
                            })
                        except Exception as e:
                            logger.error(f"Error in sidebar chatbot interface: {e}", exc_info=True)
                            st.error("Assistant encountered a processing error. Please try again.")
        
        interaction.update({
            "start": start_location,
            "end": end_location,
            "algorithm": algorithm,
            "run_pathfinding": run_pathfinding,
            "run_comparison": run_comparison,
            "run_heuristic_comparison": run_heuristic_comparison,
            "ai_triggered_path": ai_triggered_path
        })
        
        return interaction
