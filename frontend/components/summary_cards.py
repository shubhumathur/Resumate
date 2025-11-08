"""
Summary cards component for displaying candidate summaries.
"""
import streamlit as st
from typing import List, Dict


def render_summary_cards(results: List[Dict]):
    """
    Render summary cards for each candidate.
    
    Args:
        results: List of matching results with summaries
    """
    st.header("📋 Candidate Summaries")
    
    if not results:
        st.warning("No summaries to display.")
        return
    
    # Display cards
    for idx, result in enumerate(results):
        candidate_name = result.get("candidate_name", "Unknown")
        suitability_score = result.get("suitability_score", 0)
        summary = result.get("summary", "No summary available.")
        
        # Determine color based on score
        if suitability_score >= 80:
            color = "🟢"
        elif suitability_score >= 60:
            color = "🟡"
        else:
            color = "🔴"
        
        with st.expander(f"{color} {candidate_name} - {suitability_score}% Suitability", expanded=(idx < 3)):
            st.markdown(f"**Suitability Score:** {suitability_score}%")
            
            # Summary
            st.subheader("Summary")
            st.write(summary)
            
            # Matching details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                semantic_similarity = result.get("semantic_similarity", 0)
                st.metric("Semantic Similarity", f"{semantic_similarity}%")
            
            with col2:
                skill_overlap = result.get("skill_overlap", 0)
                st.metric("Skill Overlap", f"{skill_overlap}%")
            
            with col3:
                experience_relevance = result.get("experience_relevance", 0)
                st.metric("Experience Relevance", f"{experience_relevance}%")
            
            # Matching skills
            matching_skills = result.get("matching_skills", [])
            if matching_skills:
                st.subheader("✅ Matching Skills")
                st.write(", ".join(matching_skills[:15]))
            
            # Missing skills
            missing_skills = result.get("missing_skills", [])
            if missing_skills:
                st.subheader("❌ Missing Skills")
                st.write(", ".join(missing_skills[:10]))
            
            # Interview questions
            questions = result.get("questions", [])
            if questions:
                st.subheader("💡 Suggested Interview Questions")
                for q_idx, question in enumerate(questions, 1):
                    st.write(f"{q_idx}. {question}")

