import streamlit as st
import pandas as pd
from src.logger import logger

def render_algorithm_comparison(pathfinder):
    """Renders the algorithm comparison dataframes and key metrics."""
    st.markdown("---")
    st.subheader("📊 Algorithm Performance Comparison")
    
    with st.spinner("🔬 Running algorithm comparison..."):
        try:
            comparison_results = pathfinder.compare_algorithms()
            
            # Display results table
            df = pd.DataFrame(comparison_results)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            # Performance insights
            st.subheader("💡 Performance Insights")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fastest_algo = df.loc[df['Average Distance (m)'].idxmin(), 'Algorithm']
                st.metric("🏆 Shortest Path", str(fastest_algo))
            
            with col2:
                least_explored = df.loc[df['Average Nodes Explored'].idxmin(), 'Algorithm']
                st.metric("⚡ Most Efficient (Exploration)", str(least_explored))
            
            with col3:
                most_explored = df.loc[df['Average Nodes Explored'].idxmax(), 'Algorithm']
                st.metric("🔍 Most Thorough", str(most_explored))
                
        except Exception as e:
            logger.error(f"Error drawing algorithm comparison: {e}", exc_info=True)
            st.error("Could not complete algorithm comparison calculation.")

def render_heuristic_comparison(pathfinder):
    """Renders the heuristic performance metrics and description analysis."""
    st.markdown("---")
    st.subheader("🎯 A* Heuristic Comparison")
    
    with st.spinner("🔬 Running heuristic comparison..."):
        try:
            heuristic_results = pathfinder.compare_heuristics()
            
            # Display results table
            df_heuristic = pd.DataFrame(heuristic_results)
            st.dataframe(
                df_heuristic,
                use_container_width=True,
                hide_index=True
            )
            
            # Heuristic insights
            st.subheader("🧠 Heuristic Analysis")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                best_heuristic = df_heuristic.loc[df_heuristic['Average Distance (m)'].idxmin(), 'Heuristic Type']
                st.metric("🏆 Best Distance", str(best_heuristic))
            
            with col2:
                most_efficient = df_heuristic.loc[df_heuristic['Average Nodes Explored'].idxmin(), 'Heuristic Type']
                st.metric("⚡ Most Efficient", str(most_efficient))
            
            with col3:
                best_efficiency = df_heuristic.loc[df_heuristic['Efficiency Score'].idxmax(), 'Heuristic Type']
                st.metric("🎯 Best Efficiency Score", str(best_efficiency))
            
            st.subheader("📈 Analysis Documentation")
            st.markdown("""
            * **Euclidean Distance**: Straight-line distance calculation. Fast, admissible, and consistent for coordinate grids.
            * **Manhattan Distance**: Grid/block movement distance (sum of absolute differences in coordinates). Tends to overestimate diagonal routes.
            * **Combined Heuristic**: Weighted blend (70% Euclidean + 30% Manhattan). Balances directional coordinates with grid layout constraints.
            * **Efficiency Score**: Distance covered divided by nodes explored (higher score = better target alignment).
            """)
            
        except Exception as e:
            logger.error(f"Error drawing heuristic comparison: {e}", exc_info=True)
            st.error("Could not complete heuristic comparison calculations.")
