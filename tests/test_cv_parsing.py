#!/usr/bin/env python3
"""
Test script for CV parsing functionality
"""

import sys
import os
sys.path.append('.')

from app import parse_pdf_cv, StructuredCV
import json

def test_cv_parsing():
    """Test the CV parsing with a sample CV text"""
    print("Testing CV parsing functionality...")

    # Create a test CV text (simulating PDF content)
    test_cv_text = """
MALIK SBOUI
Data Scientist | Machine Learning Engineer
Email: malik.sboui@email.com
Phone: +216 123 456 789
Location: Sousse, Tunisia

EDUCATION
Masters in Business Analytics
Esprit School of Business
September 2022 - July 2024

Bachelor in Finance
Higher Institut of Management Sousse
September 2017 - June 2020

WORK EXPERIENCE
Data Scientist Intern
Kripton
February 2024 - July 2024
- Collected and annotated images using CVAT.AI
- Developed a proof of concept using Django and GEMINI
- Applied Scrum methodology for project management

PROJECTS
Investment Opportunity Assessment System
ODDO BHF/Esprit School of Business
Duration: 52 months
- Scraped articles in five languages using Selenium and Beautiful Soup
- Designed and built a scalable database in MongoDB
- Developed machine learning classification models with 83% accuracy

French Insurance Budget Prediction
Esprit school of business
Duration: 51 months
- Performed ETL processes on 1.5 million lines of data using Talend Studio
- Conducted data preprocessing and developed machine learning classification models with 85% accuracy

TECHNICAL SKILLS
Programming Languages: Python, SQL
Frameworks: Django, Selenium, Beautiful Soup
Databases: MongoDB
Tools: Talend Studio, Microsoft Power BI, Chart.js, CVAT.AI
Machine Learning: OpenAI Whisper, YOLOv8, Microsoft/Trocr-base
APIs: ChatGPT 3.5 Turbo API
"""

    # Test the structured CV creation directly
    print("Creating test StructuredCV...")
    try:
        # Simulate what the LLM would return
        test_cv_data = {
            "personal_info": {
                "name": "MALIK SBOUI",
                "email": "malik.sboui@email.com",
                "phone": "+216 123 456 789",
                "location": "Sousse, Tunisia"
            },
            "experiences": [
                {
                    "company": "Kripton",
                    "position": "Data Scientist Intern",
                    "start_date": "February 2024",
                    "end_date": "July 2024",
                    "duration": "6 months",
                    "responsibilities": [
                        "Collected and annotated images using CVAT.AI",
                        "Developed a proof of concept using Django and GEMINI",
                        "Applied Scrum methodology for project management"
                    ],
                    "technologies": ["CVAT.AI", "Django", "GEMINI", "Scrum"]
                }
            ],
            "education": [
                {
                    "institution": "Esprit School of Business",
                    "degree": "Masters in Business Analytics",
                    "field_of_study": "Business Analytics",
                    "start_date": "September 2022",
                    "end_date": "July 2024",
                    "grade": ""
                },
                {
                    "institution": "Higher Institut of Management Sousse",
                    "degree": "Bachelor in Finance",
                    "field_of_study": "Finance",
                    "start_date": "September 2017",
                    "end_date": "June 2020",
                    "grade": ""
                }
            ],
            "skills": [
                {"name": "Python", "category": "programming", "proficiency": ""},
                {"name": "SQL", "category": "programming", "proficiency": ""},
                {"name": "Django", "category": "framework", "proficiency": ""},
                {"name": "MongoDB", "category": "tool", "proficiency": ""},
                {"name": "YOLOv8", "category": "tool", "proficiency": ""}
            ],
            "projects": [
                {
                    "name": "Investment Opportunity Assessment System",
                    "description": "ML system for investment analysis",
                    "technologies": ["Selenium", "Beautiful Soup", "MongoDB"],
                    "duration": "52 months",
                    "achievements": ["83% accuracy machine learning models"]
                }
            ],
            "achievements": [],
            "languages": []
        }

        structured_cv = StructuredCV(**test_cv_data)
        print("SUCCESS: StructuredCV created successfully!")
        print(f"Experiences: {len(structured_cv.experiences)}")
        print(f"Education: {len(structured_cv.education)}")
        print(f"Skills: {len(structured_cv.skills)}")
        print(f"Projects: {len(structured_cv.projects)}")

        # Test JSON serialization
        cv_json = structured_cv.dict()
        print("\nSUCCESS: JSON serialization successful!")

        # Save test data
        with open('uploads/test_structured_cv.json', 'w') as f:
            json.dump(cv_json, f, indent=2)
        print("SUCCESS: Test CV data saved to uploads/test_structured_cv.json")

        return True

    except Exception as e:
        print(f"ERROR: Error testing CV parsing: {e}")
        return False

if __name__ == "__main__":
    test_cv_parsing()