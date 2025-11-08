"""
Streamlit frontend application for ResuMate.
"""
import streamlit as st
import requests
import json
from typing import List, Dict, Tuple
import pandas as pd
from io import BytesIO

# Import components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.upload_section import render_upload_section
from components.results_table import render_results_table
from components.summary_cards import render_summary_cards
from components.graph_visuals import render_graph_visuals, render_skill_overlap_chart

# Configure page
st.set_page_config(
    page_title="ResuMate - Intelligent Resume Screening",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = "http://localhost:8000"


def check_api_connection() -> bool:
    """Check if API is available."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def process_resumes_and_jd(
    resume_files: List[bytes],
    resume_filenames: List[str],
    jd_text: str
) -> Dict:
    """
    Process resumes and job description through the API.
    
    Args:
        resume_files: List of resume file contents
        resume_filenames: List of resume filenames
        jd_text: Job description text
        
    Returns:
        Processing results
    """
    try:
        # First, parse the job description
        jd_response = requests.post(
            f"{API_BASE_URL}/parse_jd",
            json={"jd_text": jd_text},
            timeout=30
        )
        jd_response.raise_for_status()
        jd_data = jd_response.json()["data"]
        
        # Parse all resumes
        resumes_data = []
        for resume_file, filename in zip(resume_files, resume_filenames):
            # Prepare file for upload
            files = {
                "file": (filename, BytesIO(resume_file))
            }
            
            resume_response = requests.post(
                f"{API_BASE_URL}/parse_resume_file",
                files=files,
                timeout=30
            )
            resume_response.raise_for_status()
            resume_data = resume_response.json()["data"]
            resumes_data.append(resume_data)
        
        # Match all resumes
        match_response = requests.post(
            f"{API_BASE_URL}/batch_match",
            json={
                "resumes_data": resumes_data,
                "jd_data": jd_data
            },
            timeout=60
        )
        match_response.raise_for_status()
        match_results = match_response.json()["data"]
        
        # Generate summaries and questions for each result
        results = []
        for match_result in match_results:
            # Generate summary
            summary_response = requests.post(
                f"{API_BASE_URL}/generate_summary",
                json={"match_result": match_result},
                timeout=30
            )
            summary_response.raise_for_status()
            summary = summary_response.json()["summary"]
            
            # Generate questions
            questions_response = requests.post(
                f"{API_BASE_URL}/generate_questions",
                json={
                    "resume_data": match_result["resume_data"],
                    "jd_data": match_result["jd_data"],
                    "num_questions": 5
                },
                timeout=30
            )
            questions_response.raise_for_status()
            questions = questions_response.json()["questions"]
            
            results.append({
                **match_result,
                "summary": summary,
                "questions": questions
            })
        
        return {"success": True, "results": results, "jd_data": jd_data}
    
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return {"success": False, "error": str(e)}


def export_results_to_csv(results: List[Dict]) -> bytes:
    """Export results to CSV format."""
    table_data = []
    for result in results:
        table_data.append({
            "Candidate": result.get("candidate_name", "Unknown"),
            "Suitability Score": result.get("suitability_score", 0),
            "Semantic Similarity": result.get("semantic_similarity", 0),
            "Skill Overlap": result.get("skill_overlap", 0),
            "Experience Relevance": result.get("experience_relevance", 0),
            "Matching Skills": ", ".join(result.get("matching_skills", [])),
            "Missing Skills": ", ".join(result.get("missing_skills", []))
        })
    
    df = pd.DataFrame(table_data)
    csv = df.to_csv(index=False)
    return csv.encode('utf-8')


def main():
    """Main application function."""
    # Title and header
    st.title("📄 ResuMate - Intelligent Resume Screening")
    st.markdown("**Agentic AI system for intelligent resume screening and candidate matching**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API URL configuration
        global API_BASE_URL
        api_url = st.text_input(
            "API Base URL",
            value=API_BASE_URL,
            help="Backend API URL (default: http://localhost:8000)"
        )
        API_BASE_URL = api_url
        
        # Check API connection
        if st.button("Check API Connection"):
            if check_api_connection():
                st.success("✅ API is connected")
            else:
                st.error("❌ API is not available. Make sure the backend is running.")
        
        st.markdown("---")
        st.markdown("### 📖 About")
        st.markdown("""
        ResuMate uses advanced NLP and LLM-based agents to:
        - Parse resumes and job descriptions
        - Compute semantic similarity
        - Generate explainable summaries
        - Suggest interview questions
        """)
    
    # Main content
    # Upload section
    resume_files, resume_filenames, jd_text = render_upload_section()
    
    # Process button
    if st.button("🚀 Process Resumes", type="primary", use_container_width=True):
        if not resume_files:
            st.error("❌ Please upload at least one resume file.")
            return
        
        if not jd_text:
            st.error("❌ Please provide a job description.")
            return
        
        # Check API connection
        if not check_api_connection():
            st.error("❌ Cannot connect to API. Please make sure the backend is running at " + API_BASE_URL)
            return
        
        # Process
        with st.spinner("Processing resumes and generating summaries..."):
            result = process_resumes_and_jd(resume_files, resume_filenames, jd_text)
        
        if result["success"]:
            # Store results in session state
            st.session_state.results = result["results"]
            st.session_state.jd_data = result.get("jd_data", {})
            st.success("✅ Processing complete!")
        else:
            st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
    
    # Display results if available
    if "results" in st.session_state and st.session_state.results:
        st.markdown("---")
        
        # Results table
        df = render_results_table(st.session_state.results)
        
        # Export button
        col1, col2 = st.columns([1, 4])
        with col1:
            csv_data = export_results_to_csv(st.session_state.results)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name="resumate_results.csv",
                mime="text/csv"
            )
        
        # Summary cards
        render_summary_cards(st.session_state.results)
        
        # Graph visualization (placeholder)
        if st.session_state.get("jd_data"):
            render_graph_visuals(
                jd_data=st.session_state.jd_data,
                results=st.session_state.results
            )
            
            # Skill overlap chart
            st.subheader("📊 Skill Overlap Analysis")
            render_skill_overlap_chart(st.session_state.results)


if __name__ == "__main__":
    main()
