#!/usr/bin/env python3
"""
Test script for question generation with structured CV
"""

import sys
import os
sys.path.append('.')

from app import generate_question, InterviewState, StructuredCV, load_text_file
import json

def test_question_generation():
    """Test enhanced question generation with structured CV"""
    print("Testing enhanced question generation...")

    try:
        # Load job description
        job_description = load_text_file('uploads/job_description.txt')
        print(f"Job description loaded: {len(job_description)} characters")

        # Load structured CV
        with open('uploads/structured_cv.json', 'r') as f:
            cv_data = json.load(f)
        structured_cv = StructuredCV(**cv_data)
        print(f"Structured CV loaded: {len(structured_cv.experiences)} experiences")

        # Test question generation for each interview stage
        for question_num in range(3):
            print(f"\n=== Testing Question {question_num + 1} ===")

            # Create interview state
            state = InterviewState(
                job_description=job_description,
                cv_summary="",  # Using structured CV instead
                structured_cv=structured_cv,
                question_count=question_num,
                questions_asked=["Sample previous question"] * question_num,
                current_question="",
                complete=False,
                user_responses=["Sample response about my experience"] * question_num
            )

            # Generate question
            result = generate_question(state)

            if result.get("complete"):
                print("Interview marked as complete")
                break

            question = result.get("current_question", "No question generated")
            print(f"Generated question: {question}")
            print(f"Question length: {len(question)} characters")

            # Verify question content
            if "Kripton" in question or "Data Scientist" in question or "Django" in question:
                print("SUCCESS: Question references specific CV content")
            elif question_num == 0:
                print("NOTE: First question should reference specific CV details")

        print("\nSUCCESS: Question generation test completed!")
        return True

    except Exception as e:
        print(f"ERROR: Error testing question generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_question_generation()