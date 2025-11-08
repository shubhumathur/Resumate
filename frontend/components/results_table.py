"""
Results table component for displaying candidate rankings.
"""
import streamlit as st
import pandas as pd
from typing import List, Dict


def render_results_table(results: List[Dict]):
    """
    Render candidate ranking table.
    
    Args:
        results: List of matching results
    """
    st.header("📊 Candidate Ranking")
    
    if not results:
        st.warning("No results to display.")
        return
    
    # Prepare data for table
    table_data = []
    for result in results:
        candidate_name = result.get("candidate_name", "Unknown")
        suitability_score = result.get("suitability_score", 0)
        matching_skills = result.get("matching_skills", [])
        missing_skills = result.get("missing_skills", [])
        
        table_data.append({
            "Rank": len(table_data) + 1,
            "Candidate": candidate_name,
            "Suitability Score": f"{suitability_score}%",
            "Match Highlights": ", ".join(matching_skills[:5]) if matching_skills else "None",
            "Key Gaps": ", ".join(missing_skills[:3]) if missing_skills else "None"
        })
    
    # Create DataFrame
    df = pd.DataFrame(table_data)
    
    # Display table with styling
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Add color coding based on score
    st.markdown("""
    <style>
    .score-high { color: #00cc00; }
    .score-medium { color: #ffaa00; }
    .score-low { color: #ff0000; }
    </style>
    """, unsafe_allow_html=True)
    
    # Display summary statistics
    if table_data:
        avg_score = sum(float(r["Suitability Score"].replace("%", "")) for r in table_data) / len(table_data)
        max_score = max(float(r["Suitability Score"].replace("%", "")) for r in table_data)
        min_score = min(float(r["Suitability Score"].replace("%", "")) for r in table_data)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Score", f"{avg_score:.1f}%")
        with col2:
            st.metric("Highest Score", f"{max_score:.1f}%")
        with col3:
            st.metric("Lowest Score", f"{min_score:.1f}%")
    
    return df

