"""
Setup script for ResuMate.
"""
from setuptools import setup, find_packages

setup(
    name="resumate",
    version="1.0.0",
    description="Intelligent Resume Screening and Candidate Matching System",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "python-multipart>=0.0.6",
        "streamlit>=1.29.0",
        "PyMuPDF>=1.23.8",
        "python-docx>=1.1.0",
        "spacy>=3.7.2",
        "sentence-transformers>=2.2.2",
        "scikit-learn>=1.4.0",
        "numpy>=1.26.3",
        "pandas>=2.1.4",
        "google-generativeai>=0.3.2",
        "pymongo>=4.6.1",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "aiofiles>=23.2.1",
        "requests>=2.31.0",
    ],
    python_requires=">=3.10",
)

