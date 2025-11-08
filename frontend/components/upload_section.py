"""
Upload section component for Streamlit frontend.
"""
import streamlit as st
from typing import List, Tuple
import io


def render_upload_section() -> Tuple[List[bytes], List[str], str]:
    """
    Render upload section for resumes and job description.
    
    Returns:
        Tuple of (resume_files, resume_filenames, jd_text)
    """
    st.header("📤 Upload Resumes and Job Description")
    
    # Resume upload
    st.subheader("Resumes")
    uploaded_resumes = st.file_uploader(
        "Upload resume files (PDF, DOCX, TXT)",
        type=["pdf", "docx", "doc", "txt"],
        accept_multiple_files=True,
        help="You can upload multiple resume files"
    )
    
    resume_files = []
    resume_filenames = []
    
    if uploaded_resumes:
        for resume in uploaded_resumes:
            resume_files.append(resume.read())
            resume_filenames.append(resume.name)
            st.success(f"✅ Uploaded: {resume.name}")
    
    # Job description upload
    st.subheader("Job Description")
    
    jd_option = st.radio(
        "Choose input method:",
        ["Text Input", "File Upload"],
        horizontal=True
    )
    
    jd_text = ""
    
    if jd_option == "Text Input":
        jd_text = st.text_area(
            "Enter job description:",
            height=300,
            placeholder="Paste the job description here..."
        )
    else:
        jd_file = st.file_uploader(
            "Upload job description file",
            type=["pdf", "docx", "doc", "txt"],
            help="Upload a PDF, DOCX, or TXT file containing the job description"
        )
        
        if jd_file:
            jd_text = jd_file.read().decode('utf-8', errors='ignore')
            st.success(f"✅ Uploaded: {jd_file.name}")
    
    return resume_files, resume_filenames, jd_text

